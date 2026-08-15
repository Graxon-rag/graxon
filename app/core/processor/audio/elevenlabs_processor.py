from elevenlabs.types.speech_to_text_chunk_response_model import SpeechToTextChunkResponseModel
from app.providers.audio.elevenlabs import ElevenlabsAudioProvider
from .model import AudioProviderEnum, Utterance, Transcript, Word
from langchain_core.documents import Document
from .chunk_builder import build_documents
from typing import Tuple, List, Optional
from app.utils.logger import logger
from .base import AudioProcessor
from pydub import AudioSegment
from pathlib import Path
import asyncio
import math


ELEVENLABS_TEMP_DIR = Path("temp/audio/elevenlabs")


class ElevenlabsAudioProcessor(AudioProcessor):
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

        # ElevenLabs config
        base_url: str = "https://api.elevenlabs.io",
        model_id: str = "scribe_v2",
        tag_audio_events: bool = True,
        diarize: bool = True,
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

        self.model_id = model_id
        self.tag_audio_events = tag_audio_events
        self.diarize = diarize

        self._client = ElevenlabsAudioProvider(
            api_key=api_key,
            timeout=timeout,
            base_url=base_url,
        )

        ELEVENLABS_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Level 1: Slice audio at file_chunk_number * segment_duration_min via pydub
        Level 2: Transcribe with ElevenLabs Scribe, normalize to Transcript schema
        Level 3: Group utterances into RAG chunks (whichever guard fires first):
                 - accumulated duration >= max_time_per_rag_chunk_min
                 - accumulated word count >= max_words_per_rag_chunk

        Returns:
            documents:             list of Document (one per RAG chunk)
            next_rag_chunk_index:  pass as rag_chunk_start_index to next message
            is_last:               True if this was the final audio segment
        """
        audio_slice_path, is_last = await asyncio.to_thread(self._slice_audio)
        transcript = await self._transcribe(audio_slice_path)
        documents = build_documents(transcript, self.filename, self.file_chunk_number, self.rag_chunk_start_index, self.max_time_per_rag_chunk_ms, self.max_words_per_rag_chunk, self.diarize, str(self.file_path))
        return documents, self.rag_chunk_start_index + len(documents), is_last

    async def _transcribe(self, audio_path: Path) -> Transcript:
        """
        Transcribes audio slice with ElevenLabs Scribe.
        Mirrors your reference code exactly.

        Note:
          - Word-level iteration (no utterance object from API — we build them)
          - Speaker changes detected at word level (same as Deepgram)
          - Confidence from logprob: math.exp(logprob) → 0-1 range
          - Skips "spacing" type words (ElevenLabs-specific token type)
          - Timestamps already in seconds — just add offset
        """
        offset_sec = self.file_chunk_number * self.segment_duration_min * 60

        client = await self._client.client()

        logger.info({
            "message": "Transcribing audio slice",
            "audio_path": str(audio_path),
            "model_id": self.model_id,
        })

        transcription = await client.speech_to_text.convert(
            model_id=self.model_id,
            file=audio_path.read_bytes(),
            tag_audio_events=self.tag_audio_events,
            diarize=self.diarize,
        )

        if not isinstance(transcription, SpeechToTextChunkResponseModel):
            raise RuntimeError(
                f"ElevenLabs returned unexpected response type: {type(transcription)}"
            )

        if not transcription.words:
            return Transcript(
                provider=AudioProviderEnum.ELEVENLABS,
                source_file=str(audio_path),
                language=getattr(transcription, "language_code", None),
                duration=getattr(transcription, "audio_duration_secs", None),
            )

        # Iterate words, group into utterances by speaker change
        final_utterances: List[Utterance] = []
        current_speaker: Optional[str] = None
        current_words: List[Word] = []

        for word_obj in transcription.words:
            # Skip spacing tokens — ElevenLabs-specific, not real words
            if word_obj.type == "spacing":
                continue

            speaker = str(word_obj.speaker_id) if word_obj.speaker_id else "unknown"

            if current_speaker is None:
                current_speaker = speaker

            if speaker != current_speaker:
                if current_words:
                    final_utterances.append(
                        self._make_utterance(current_words, current_speaker)
                    )
                current_speaker = speaker
                current_words = []

            # Convert logprob → confidence (0-1)
            logprob = word_obj.logprob
            confidence = round(math.exp(logprob), 4) if logprob is not None else None

            current_words.append(Word(
                text=word_obj.text.strip(),
                # Timestamps already in seconds — add offset for original-file alignment
                start=None if word_obj.start is None else word_obj.start + offset_sec,
                end=None if word_obj.end is None else word_obj.end + offset_sec,
                confidence=confidence,
                speaker=speaker,
            ))

        # Flush last group
        if current_words:
            final_utterances.append(
                self._make_utterance(current_words, current_speaker or "unknown")
            )

        return Transcript(
            provider=AudioProviderEnum.ELEVENLABS,
            utterances=final_utterances,
            language=getattr(transcription, "language_code", None),
            source_file=str(audio_path),
            duration=getattr(transcription, "audio_duration_secs", None),
        )

    @staticmethod
    def _make_utterance(words: List[Word], speaker: str) -> Utterance:
        """Builds Utterance from words. Start/end already offset-adjusted."""
        return Utterance(
            text=" ".join(w.text for w in words),
            start=words[0].start,
            end=words[-1].end,
            speaker=speaker,
            words=words,
        )

    def _slice_audio(self) -> Tuple[Path, bool]:

        logger.info({
            "message": "elevenlabs audio processor is slicing audio",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "segment_duration_ms": self.segment_duration_ms,
            "model_id": self.model_id,
            "diarize": self.diarize
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
        slice_path = ELEVENLABS_TEMP_DIR / f"{self.file_path.stem}_chunk_{self.file_chunk_number}.mp3"
        audio[start_ms:end_ms].export(str(slice_path), format="mp3")

        logger.info({
            "message": "elevenlabs audio processor sliced audio",
            "file_path": str(self.file_path),
            "file_chunk_number": self.file_chunk_number,
            "slice_path": str(slice_path),
        })

        return slice_path, is_last
