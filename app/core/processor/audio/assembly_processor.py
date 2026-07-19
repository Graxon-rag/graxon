from app.providers.audio.assembly import AssemblyAudioProvider, aai
from .model import Utterance, Transcript, Word
from langchain_core.documents import Document
from .chunk_builder import build_documents
from app.utils.logger import logger
from .base import AudioProcessor
from typing import Tuple, List
from pydub import AudioSegment
from pathlib import Path
import asyncio


ASSEMBLY_TEMP_DIR = Path("temp/audio/assembly")


class AssemblyAudioProcessor(AudioProcessor):
    def __init__(
        self,
        file_path: str,
        filename: str,
        api_key: str,
        file_chunk_number: int,            # which audio segment (0, 1, 2, ...)
        rag_chunk_start_index: int,        # absolute RAG chunk index to continue from

        # Level 1 — audio file splitting
        segment_duration_min: float = 10,  # minutes per audio IO buffer

        # Level 2 — RAG chunking from utterances
        max_time_per_rag_chunk_min: float = 2.0,   # max minutes per RAG chunk
        max_words_per_rag_chunk: int = 300,         # max words per RAG chunk

        # AssemblyAI config

        speaker_labels: bool = True,
        language_detection: bool = True,
    ):
        self.file_path = Path(file_path)
        self.filename = filename
        self.file_chunk_number = file_chunk_number
        self.rag_chunk_start_index = rag_chunk_start_index

        self.segment_duration_ms = int(segment_duration_min * 60 * 1000)  # pydub uses ms
        self.segment_duration_min = segment_duration_min
        self.max_time_per_rag_chunk_ms = int(max_time_per_rag_chunk_min * 60 * 1000)
        self.max_words_per_rag_chunk = max_words_per_rag_chunk

        self.speaker_labels = speaker_labels
        self.language_detection = language_detection

        self._client = AssemblyAudioProvider(api_key)
        ASSEMBLY_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Level 1: Slice audio file at file_chunk_number * segment_duration_min
                 using pydub — save to temp/{stem}_chunk_{n}.mp3
        Level 2: Transcribe the slice with AssemblyAI
                 Normalize to Transcript schema
        Level 3: Group utterances into RAG chunks by whichever guard fires first:
                 - accumulated duration >= max_time_per_rag_chunk_min
                 - accumulated word count >= max_words_per_rag_chunk
                 Each group → one Document

        Returns:
            documents:             list of Document (one per RAG chunk)
            next_rag_chunk_index:  pass as rag_chunk_start_index to next message
            is_last:               True if this was the final audio segment
        """
        # --- Level 1: slice audio ---
        audio_slice_path, is_last = self._slice_audio()

        # --- Level 2: transcribe + normalize ---
        transcript = await self._transcribe(audio_slice_path)

        # --- Level 3: group utterances into RAG chunks ---
        documents = build_documents(transcript, self.filename, self.file_chunk_number, self.rag_chunk_start_index, self.max_time_per_rag_chunk_ms, self.max_words_per_rag_chunk, self.speaker_labels, str(self.file_path))

        return documents, self.rag_chunk_start_index + len(documents), is_last

    async def _transcribe(self, audio_path: Path) -> Transcript:
        """
        Transcribes the audio slice with AssemblyAI.
        Normalizes the response to the universal Transcript schema.
        Mirrors your reference code exactly.
        """
        config = aai.TranscriptionConfig(
            speaker_labels=self.speaker_labels,
            language_detection=self.language_detection,
        )

        client = await self._client.client()

        transcriber = client.Transcriber()

        logger.info({
            "message": "Transcribing audio",
            "file_path": str(audio_path),
            "file_chunk_number": self.file_chunk_number,
        })

        # AssemblyAI SDK uses concurrent.futures — wrap for async
        future = transcriber.transcribe_async(str(audio_path), config=config)
        result = await asyncio.wrap_future(future)

        if result.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI transcription failed: {result.error}")

        if not result.utterances:
            return Transcript(
                provider="assemblyai",
                source_file=str(audio_path),
                duration=result.audio_duration,
                language=result.language_code,
            )

        logger.info({
            "message": "Transcription complete",
            "file_path": str(audio_path),
            "file_chunk_number": self.file_chunk_number,
            "num_utterances": len(result.utterances),
        })

        offset_sec = self.file_chunk_number * self.segment_duration_min * 60

        # Normalize to schema
        utterances: List[Utterance] = []

        logger.info({
            "message": "Normalizing utterances",
            "file_path": str(audio_path),
            "file_chunk_number": self.file_chunk_number,
            "num_utterances": len(result.utterances),
        })

        for u in result.utterances:
            words: List[Word] = [
                Word(
                    text=w.text,
                    start=None if w.start is None else (w.start / 1000) + offset_sec,  # ms → seconds
                    end=None if w.end is None else (w.end / 1000) + offset_sec,
                    confidence=w.confidence,
                    speaker=w.speaker,
                )
                for w in (u.words or [])
            ]

            utterances.append(Utterance(
                text=u.text,
                start=offset_sec if u.start is None else (u.start / 1000) + offset_sec,  # ms → seconds
                end=None if u.end is None else (u.end / 1000) + offset_sec,
                speaker=str(u.speaker) if u.speaker else None,
                confidence=u.confidence,
                words=words,
            ))

        return Transcript(
            provider="assemblyai",
            utterances=utterances,
            language=result.language_code,
            source_file=str(audio_path),
            duration=result.audio_duration,
        )

    def _slice_audio(self) -> Tuple[Path, bool]:
        """
        Loads the full audio file, extracts the segment at file_chunk_number offset.
        Saves to temp/{stem}_chunk_{n}.mp3

        Uses pydub ms-based slicing:
            audio[start_ms : end_ms]

        Returns: (slice_path, is_last)
        """
        logger.info({
            "message": "Slicing audio",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "segment_duration_min": self.segment_duration_min,
            "speaker_labels": self.speaker_labels,
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
        audio_slice = audio[start_ms:end_ms]

        slice_path = ASSEMBLY_TEMP_DIR / f"{self.file_path.stem}_chunk_{self.file_chunk_number}.mp3"
        audio_slice.export(str(slice_path), format="mp3")

        logger.info({
            "message": "Audio sliced",
            "slice_path": str(slice_path),
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "is_last": is_last,
        })

        return slice_path, is_last
