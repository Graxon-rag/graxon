from .model import AudioProviderEnum, Utterance, Transcript, Word
from app.providers.audio.gladia import GladiaAudioProvider
from langchain_core.documents import Document
from .chunk_builder import build_documents
from typing import Tuple, List, Optional
from app.utils.logger import logger
from .base import AudioProcessor
from pydub import AudioSegment
from pathlib import Path


GLADIA_TEMP_DIR = Path("temp/audio/gladia")


class GladiaAudioProcessor(AudioProcessor):
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

        # Gladia config
        model: str = "solaria-3",
        diarization: bool = True,
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
        self.diarization = diarization
        self.timeout = timeout

        self._client = GladiaAudioProvider(api_key, timeout=timeout)

        GLADIA_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Level 1: Slice audio at file_chunk_number * segment_duration_min via pydub
        Level 2: Transcribe with Gladia Solaria, normalize to Transcript schema
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
        documents = build_documents(transcript, self.filename, self.file_chunk_number, self.rag_chunk_start_index, self.max_time_per_rag_chunk_ms, self.max_words_per_rag_chunk, self.diarization, str(self.file_path))
        return documents, self.rag_chunk_start_index + len(documents), is_last

    def _slice_audio(self) -> Tuple[Path, bool]:

        logger.info({
            "message": "Slicing audio",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "segment_duration_ms": self.segment_duration_ms,
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
        slice_path = GLADIA_TEMP_DIR / f"{self.file_path.stem}_chunk_{self.file_chunk_number}.mp3"
        audio[start_ms:end_ms].export(str(slice_path), format="mp3")

        logger.info({
            "message": "Audio sliced",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "slice_path": str(slice_path),
        })

        return slice_path, is_last

    async def _transcribe(self, audio_path: Path) -> Transcript:
        """
        Transcribes audio slice with Gladia Solaria.
        Mirrors your reference code exactly.

        Notes:
          - Gladia returns utterances directly (no word-level speaker splitting needed)
          - Speaker is an int (0, 1, 2) — coerce to str, -1 → "unknown"
          - Timestamps already in seconds — just add offset
          - Language comes from transcription.languages[0]
          - Duration from result.metadata.audio_duration
        """
        offset_sec = self.file_chunk_number * self.segment_duration_min * 60

        client = await self._client.client()

        logger.info({
            "message": "Transcribing audio slice",
            "audio_path": str(audio_path),
            "model": self.model,
            "diarization": self.diarization,
        })

        response = await client.transcribe(
            audio_path,
            options={
                "model": self.model,
                "diarization": self.diarization,
            },
            timeout=self.timeout,
        )

        logger.info({
            "message": "Audio transcribed",
            "audio_path": str(audio_path),
            "model": self.model,
        })

        duration: Optional[float] = (
            response.result.metadata.audio_duration
            if response.result and response.result.metadata
            else None
        )
        language: Optional[str] = None
        final_utterances: List[Utterance] = []

        logger.info({
            "message": "Building transcript",
            "audio_path": str(audio_path),
            "model": self.model,
        })

        if response.result and response.result.transcription:
            trans = response.result.transcription

            if trans.languages:
                language = trans.languages[0]

            for utt in (trans.utterances or []):
                if not utt.words:
                    continue

                speaker = (
                    str(utt.speaker)
                    if utt.speaker is not None and utt.speaker >= 0
                    else "unknown"
                )

                utt_words: List[Word] = [
                    Word(
                        text=w.word,
                        # Timestamps already in seconds — add offset for original-file alignment
                        start=None if w.start is None else w.start + offset_sec,
                        end=None if w.end is None else w.end + offset_sec,
                        confidence=w.confidence,
                        speaker=speaker,
                    )
                    for w in utt.words
                ]

                final_utterances.append(Utterance(
                    text=utt.text,
                    start=None if utt.start is None else utt.start + offset_sec,
                    end=None if utt.end is None else utt.end + offset_sec,
                    speaker=speaker,
                    confidence=utt.confidence,
                    words=utt_words,
                ))

        return Transcript(
            provider=AudioProviderEnum.GLADIA,
            utterances=final_utterances,
            source_file=str(audio_path),
            duration=duration,
            language=language,
        )
