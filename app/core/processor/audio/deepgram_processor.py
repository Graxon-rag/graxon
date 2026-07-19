from .model import Utterance, Transcript, Word, AudioProviderEnum
from deepgram.types.listen_v1response import ListenV1Response
from app.providers.audio.deepgram import DeepgramProvider
from langchain_core.documents import Document
from .chunk_builder import build_documents
from typing import Tuple, List, Optional
from app.utils.logger import logger
from .base import AudioProcessor
from pydub import AudioSegment
from pathlib import Path


DEEPGRAM_TEMP_DIR = Path("temp/audio/deepgram")


class DeepgramAudioProcessor(AudioProcessor):
    def __init__(
        self,
        file_path: str,
        filename: str,
        api_key: str,
        file_chunk_number: int,             # which audio segment (0, 1, 2, ...)
        rag_chunk_start_index: int,         # absolute RAG chunk index to continue from

        # Level 1 — audio file splitting
        segment_duration_min: float = 10,   # minutes per audio IO buffer

        # Level 2 — RAG chunking from utterances
        max_time_per_rag_chunk_min: float = 2.0,
        max_words_per_rag_chunk: int = 300,

        # Deepgram config
        model: str = "nova-3",
        diarize: bool = True,
        smart_format: bool = True,
        detect_language: bool = True,
        timeout: float = 60 * 10
    ):
        self.file_path = Path(file_path)
        self.filename = filename
        self.file_chunk_number = file_chunk_number
        self.rag_chunk_start_index = rag_chunk_start_index

        self.segment_duration_min = segment_duration_min
        self.segment_duration_ms = int(segment_duration_min * 60 * 1000)
        self.max_time_per_rag_chunk_ms = int(max_time_per_rag_chunk_min * 60 * 1000)
        self.max_words_per_rag_chunk = max_words_per_rag_chunk

        self.model = model
        self.diarize = diarize
        self.smart_format = smart_format
        self.detect_language = detect_language

        self._client = DeepgramProvider(api_key, timeout=timeout)

        DEEPGRAM_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Level 1: Slice audio at file_chunk_number * segment_duration_min via pydub
        Level 2: Transcribe with Deepgram Nova-3, normalize to Transcript schema
        Level 3: Group utterances into RAG chunks (whichever guard fires first):
                 - accumulated duration >= max_time_per_rag_chunk_min
                 - accumulated word count >= max_words_per_rag_chunk

        Returns:
            documents:             list of Document (one per RAG chunk)
            next_rag_chunk_index:  pass as rag_chunk_start_index to next message
            is_last:               True if this was the final audio segment
        """

        audio_slice_path, is_last = self._slice_audio()
        transcript = await self._transcribe(audio_slice_path)
        documents = build_documents(transcript, self.filename, self.file_chunk_number, self.rag_chunk_start_index, self.max_time_per_rag_chunk_ms, self.max_words_per_rag_chunk, self.diarize, str(self.file_path))
        return documents, self.rag_chunk_start_index + len(documents), is_last

    # Level 1 — Audio slicing (identical to AssemblyAIProcessor)
    def _slice_audio(self) -> Tuple[Path, bool]:

        logger.info({
            "message": "Slicing audio",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "segment_duration_ms": self.segment_duration_ms,
            }
        )
        audio = AudioSegment.from_file(str(self.file_path))
        total_ms = len(audio)

        start_ms = self.file_chunk_number * self.segment_duration_ms
        end_ms = min(start_ms + self.segment_duration_ms, total_ms)

        if start_ms >= total_ms:
            raise ValueError(
                f"file_chunk_number={self.file_chunk_number} is out of range. "
                f"Audio duration: {total_ms / 1000:.1f}s, "
                f"segment_duration: {self.segment_duration_ms / 1000:.1f}s"
            )

        is_last = end_ms >= total_ms
        slice_path = DEEPGRAM_TEMP_DIR / f"{self.file_path.stem}_chunk_{self.file_chunk_number}.mp3"
        audio[start_ms:end_ms].export(str(slice_path), format="mp3")

        logger.info({
            "message": "Audio sliced",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "slice_path": str(slice_path),
            "is_last": is_last,
        })

        return slice_path, is_last

    # Level 2 — Deepgram transcription + normalize to Transcript schema
    async def _transcribe(self, audio_path: Path) -> Transcript:
        """
        Transcribes audio slice with Deepgram Nova-3.
        Normalizes utterances from the response — mirrors your reference code exactly.

        Note: 
          Deepgram's utterances may have speaker changes MID-utterance (word level),
          so we split on speaker changes within each utterance (create_utterance logic).
          Timestamps are already in seconds — no ms conversion needed.
          Offset is added to make timestamps relative to the original full file.
        """
        offset_sec = self.file_chunk_number * self.segment_duration_min * 60

        client = await self._client.client()

        logger.info({
            "message": "Transcribing audio slice",
            "audio_path": str(audio_path),
            "model": self.model,
            "smart_format": self.smart_format,
            "diarize": self.diarize,
            "detect_language": self.detect_language,
        })

        response = await client.listen.v1.media.transcribe_file(
            request=audio_path.read_bytes(),
            model=self.model,
            smart_format=self.smart_format,
            diarize=self.diarize,
            utterances=True,
            detect_language=self.detect_language,
        )

        logger.info({
            "message": "Audio transcribed",
            "audio_path": str(audio_path),
        })

        if not isinstance(response, ListenV1Response):
            raise RuntimeError(
                f"Deepgram returned unexpected response type: {type(response)}"
            )

        logger.info({"message": "Normalizing utterances", "audio_path": str(audio_path)})

        duration = response.metadata.duration if response.metadata else None
        language = (
            response.results.channels[0].detected_language
            if response.results and response.results.channels
            else None
        )

        raw_utterances = (
            response.results.utterances
            if response.results and response.results.utterances
            else []
        )

        if not raw_utterances:
            return Transcript(
                provider=AudioProviderEnum.DEEPGRAM,
                source_file=str(audio_path),
                duration=duration,
                language=language,
            )

        # Normalize — split on mid-utterance speaker changes (your reference approach)
        final_utterances: List[Utterance] = []

        for utt in raw_utterances:
            if not utt.words:
                continue

            current_speaker: Optional[str] = None
            current_words: List[Word] = []

            for raw_word in utt.words:
                word_speaker = str(raw_word.speaker)

                if current_speaker is None:
                    current_speaker = word_speaker

                if word_speaker != current_speaker:
                    # Speaker changed — flush current group
                    if current_words:
                        final_utterances.append(
                            self._make_utterance(current_words, current_speaker, offset_sec)
                        )
                    current_speaker = word_speaker
                    current_words = []

                text = raw_word.punctuated_word or raw_word.word or ""
                current_words.append(Word(
                    text=text,
                    # Deepgram gives seconds directly — just add offset
                    start=None if raw_word.start is None else raw_word.start + offset_sec,
                    end=None if raw_word.end is None else raw_word.end + offset_sec,
                    confidence=raw_word.confidence,
                    speaker=word_speaker,
                ))

            # Flush last group
            if current_words:
                final_utterances.append(
                    self._make_utterance(current_words, current_speaker or "unknown", offset_sec)
                )

        return Transcript(
            provider=AudioProviderEnum.DEEPGRAM,
            utterances=final_utterances,
            source_file=str(audio_path),
            duration=duration,
            language=language,
        )

    @staticmethod
    def _make_utterance(words: List[Word], speaker: str, offset_sec: float) -> Utterance:
        """
        Builds an Utterance from a list of Words.
        Text is reconstructed by joining word texts.
        Start/end taken from first/last word (already offset-adjusted).
        """
        text = " ".join(w.text for w in words)
        return Utterance(
            text=text,
            start=words[0].start,
            end=words[-1].end,
            speaker=speaker,
            words=words,
        )
