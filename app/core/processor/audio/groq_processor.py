from .model import AudioProviderEnum, Utterance, Transcript, Word
from app.providers.audio.groq import GroqAudioProvider
from langchain_core.documents import Document
from .chunk_builder import build_documents
from app.utils.logger import logger
from .base import AudioProcessor
from typing import Tuple, List
from pydub import AudioSegment
from pathlib import Path


GROQ_TEMP_DIR = Path("temp/audio/groq")


class GroqAduioProcessor(AudioProcessor):
    def __init__(
        self,
        file_path: str,
        filename: str,
        api_key: str,
        file_chunk_number: int,
        rag_chunk_start_index: int,

        # Level 1 — audio file splitting
        segment_duration_min: float = 10,

        # Level 2 — RAG chunking from utterances
        max_time_per_rag_chunk_min: float = 2.0,
        max_words_per_rag_chunk: int = 300,

        # Groq config
        model: str = "whisper-large-v3",
        timeout: float = 60 * 10,
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

        self._client = GroqAudioProvider(api_key=api_key, timeout=timeout)

        GROQ_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Level 1: Slice audio at file_chunk_number * segment_duration_min via pydub
        Level 2: Transcribe with Groq Whisper, normalize to Transcript schema
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
        documents = build_documents(transcript, self.filename, self.file_chunk_number, self.rag_chunk_start_index, self.max_time_per_rag_chunk_ms, self.max_words_per_rag_chunk, False, str(self.file_path))
        return documents, self.rag_chunk_start_index + len(documents), is_last

    def _slice_audio(self) -> Tuple[Path, bool]:

        logger.info({
            "message": "Slicing audio",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
        })

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
        slice_path = GROQ_TEMP_DIR / f"{self.file_path.stem}_chunk_{self.file_chunk_number}.mp3"
        audio[start_ms:end_ms].export(str(slice_path), format="mp3")

        logger.info({
            "message": "Audio sliced",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "slice_path": str(slice_path),
            "is_last": is_last,
        })

        return slice_path, is_last

    async def _transcribe(self, audio_path: Path) -> Transcript:
        """
        Transcribes audio slice with Groq Whisper large-v3.
        Mirrors your reference code exactly.

        Key differences from other providers:
          - No diarization — Whisper has no speaker labels (speaker=None always)
          - Segments are the utterance unit (no speaker-level utterances)
          - confidence = no_speech_prob (probability of silence, not speech confidence)
          - Both dict and object response shapes handled (verbose_json can return either)
          - Timestamps already in seconds — just add offset
        """
        offset_sec = self.file_chunk_number * self.segment_duration_min * 60

        client = await self._client.client()

        logger.info({
            "message": "Transcribing audio slice",
            "audio_path": str(audio_path),
            "model": self.model,
        })

        translation = await client.audio.transcriptions.create(
            model=self.model,
            file=(audio_path.name, audio_path.read_bytes()),
            response_format="verbose_json",
            timestamp_granularities=["segment", "word"],
        )

        logger.info({
            "message": "Audio transcribed",
            "audio_path": str(audio_path),
            "model": self.model,
        })

        # Handle both dict and object response shapes
        if isinstance(translation, dict):
            segments = translation.get("segments", []) or []
            duration = translation.get("duration")
            language = translation.get("language")
        else:
            segments = getattr(translation, "segments", None) or []
            duration = getattr(translation, "duration", None)
            language = getattr(translation, "language", None)

        if not segments:
            return Transcript(
                provider=AudioProviderEnum.GROQ,
                source_file=str(audio_path),
                duration=duration,
                language=language,
            )

        logger.info({
            "message": "Normalizing utterances",
            "audio_path": str(audio_path),
            "model": self.model,
        })

        final_utterances: List[Utterance] = []        

        for seg in segments:
            # Handle both dict and object segment shapes (mirrors your reference exactly)
            if isinstance(seg, dict):
                text = seg.get("text", "")
                start = seg.get("start", 0.0)
                end = seg.get("end", 0.0)
                no_speech_prob = seg.get("no_speech_prob")
                raw_words = seg.get("words", []) or []
            else:
                text = getattr(seg, "text", "")
                start = getattr(seg, "start", 0.0)
                end = getattr(seg, "end", 0.0)
                no_speech_prob = getattr(seg, "no_speech_prob", None)
                raw_words = getattr(seg, "words", None) or []

            # Normalize word-level data if available
            words: List[Word] = []
            for w in raw_words:
                if isinstance(w, dict):
                    w_text = w.get("word", "")
                    w_start = w.get("start")
                    w_end = w.get("end")
                    w_prob = w.get("probability")
                else:
                    w_text = getattr(w, "word", "")
                    w_start = getattr(w, "start", None)
                    w_end = getattr(w, "end", None)
                    w_prob = getattr(w, "probability", None)

                words.append(Word(
                    text=w_text,
                    start=None if w_start is None else w_start + offset_sec,
                    end=None if w_end is None else w_end + offset_sec,
                    confidence=w_prob,
                    speaker=None,   # Whisper has no speaker diarization
                ))

            final_utterances.append(Utterance(
                text=text,
                start=None if start is None else start + offset_sec,
                end=None if end is None else end + offset_sec,
                speaker=None,           # Whisper has no speaker diarization
                confidence=no_speech_prob,
                words=words,
            ))

        return Transcript(
            provider=AudioProviderEnum.GROQ,
            utterances=final_utterances,
            source_file=str(audio_path),
            duration=duration,
            language=language,
        )
