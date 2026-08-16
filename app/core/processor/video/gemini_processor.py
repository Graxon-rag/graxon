from langchain_core.documents import Document
from typing import List, Tuple, Optional, Dict
from app.utils.logger import logger
from .base import VideoProcessor
from pathlib import Path
from google import genai
import asyncio
import json


GEMINI_TEMP_DIR = Path("temp/gemini")

# Mirrors TwelveLabs' SEGMENT_FIELDS — same field set/semantics so the rest
# of the pipeline (_filter_and_adjust, dedupe, _build_documents) can stay
# provider-agnostic and treat segments identically regardless of source.
SEGMENT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "number",
                        "description": "Segment start time in seconds, relative to this video slice.",
                    },
                    "end_time": {
                        "type": "number",
                        "description": "Segment end time in seconds, relative to this video slice.",
                    },
                    "topic_summary": {
                        "type": "string",
                        "description": (
                            "1-2 sentence summary of the core topic or theme of this segment. "
                            "Be dense and specific — avoid vague summaries like 'people are talking'."
                        ),
                    },
                    "keywords": {
                        "type": "string",
                        "description": (
                            "Comma-separated named entities, topics, products, and people mentioned "
                            "or visible in this segment."
                        ),
                    },
                    "transcript": {
                        "type": "string",
                        "description": (
                            "Verbatim words spoken OR sung during THIS SEGMENT'S TIME WINDOW ONLY "
                            "(from this segment's start_time to its end_time). Include song lyrics, "
                            "rap, chanting, and other vocalized words, not just conversational dialogue. "
                            "Do NOT include words from earlier or later segments, and do NOT repeat "
                            "lyrics/dialogue already captured in a previous segment — only transcribe "
                            "the portion of audio that plays specifically during this segment's own "
                            "time range. Empty string if no speech or singing occurs in this segment."
                        ),
                    },
                    "detailed_description": {
                        "type": "string",
                        "description": (
                            "A thorough description of everything visible: people, actions, setting, "
                            "objects, camera framing, movement, and any notable visual details."
                        ),
                    },
                    "setting": {
                        "type": "string",
                        "description": "Where this segment takes place: location, environment, indoor/outdoor, time of day if determinable.",
                    },
                    "people_present": {
                        "type": "string",
                        "description": "Description of any people visible: appearance, clothing, identity if known, expressions, actions.",
                    },
                    "speaker_names": {
                        "type": "string",
                        "description": "Names of speakers if identifiable from visual or audio cues, or empty string if unknown.",
                    },
                    "on_screen_text": {
                        "type": "string",
                        "description": "Any text, captions, lower thirds, titles, or graphics visible on screen, or empty string if none.",
                    },
                    "audio_description": {
                        "type": "string",
                        "description": "Non-speech audio: music genre/mood, ambient sounds, sound effects.",
                    },
                    "mood": {
                        "type": "string",
                        "description": "Emotional tone of this segment, e.g. 'intense debate', 'light-hearted', 'emotional', 'informative'.",
                    },
                    "has_speech": {
                        "type": "string",
                        "description": (
                            "'true' if there are spoken words OR sung lyrics/vocals during this "
                            "segment's own time window, 'false' if silent or instrumental-only music."
                        ),
                    },
                },
                "required": [
                    "start_time", "end_time", "topic_summary", "keywords", "transcript",
                    "detailed_description", "setting", "people_present", "speaker_names",
                    "on_screen_text", "audio_description", "mood", "has_speech",
                ],
            },
        },
    },
    "required": ["segments"],
}

SEGMENT_PROMPT = (
    "Segment this video into distinct scenes, topics, or actions. Each segment should "
    "cover one coherent topic or scene. For each segment, only report words spoken or "
    "sung during that segment's own start_time/end_time window — never repeat or "
    "pre-empt transcript text belonging to another segment. Return start_time/end_time "
    "in seconds, relative to the start of this video file."
)

OVERVIEW_PROMPT = (
    "Describe this entire video comprehensively covering: "
    "1. Who appears in the video (names, appearance, roles). "
    "2. The overall topic and purpose of the video. "
    "3. Key themes and topics discussed in chronological order. "
    "4. The setting and production style. "
    "5. Any notable moments, quotes, or visual elements. "
    "6. The tone and target audience."
)


class GeminiVideoProcessor(VideoProcessor):
    def __init__(
        self,
        file_path: str,
        filename: str,
        api_key: str,
        file_chunk_number: int,                     # which 10-min window (0, 1, 2 ...)
        rag_chunk_start_index: int,                 # absolute RAG chunk index to continue from

        # Level 1 — video slicing
        chunk_duration_min: float = 10.0,            # core window duration
        overlap_min: float = 1.0,                    # overlap on each side

        # Level 2 — RAG chunking from segments
        max_duration_per_rag_chunk_sec: float = 180.0,
        max_words_per_rag_chunk: int = 400,

        model_name: str = "gemini-3.5-flash",
        poll_interval: float = 2.0,
        timeout: float = 60 * 10,
    ):
        self.file_path = Path(file_path)
        self.filename = filename
        self.file_chunk_number = file_chunk_number
        self.rag_chunk_start_index = rag_chunk_start_index

        self.chunk_duration_sec = chunk_duration_min * 60
        self.overlap_sec = overlap_min * 60
        self.max_duration_per_rag_chunk_sec = max_duration_per_rag_chunk_sec
        self.max_words_per_rag_chunk = max_words_per_rag_chunk

        self.model_name = model_name
        self.poll_interval = poll_interval

        self._client = genai.Client(api_key=api_key)

        GEMINI_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Level 1: Slice video file into 12-min clip (10 core + 1 overlap each side)
                 using ffmpeg (async subprocess, non-blocking).
                 Saved to temp/{stem}_chunk_{n}.mp4

        Level 2: Upload slice to Gemini Files API, wait for ACTIVE state,
                 run segmentation (structured JSON) + overview (chunk 0 only)
                 concurrently.

        Level 3: Filter segments to core window only (drop overlap segments).
                 Group segments into RAG chunks by dual guard:
                   - accumulated duration >= max_duration_per_rag_chunk_sec
                   - accumulated word count >= max_words_per_rag_chunk
                 Each group → one Document. Transcript de-duplicated across
                 consecutive segments to guard against smearing.

        Returns:
            documents:             list of Document (overview at index 0 if chunk 0, plus RAG chunks)
            next_rag_chunk_index:  pass as rag_chunk_start_index to next message
            is_last:               True if this was the final video slice
        """
        # --- Level 1: slice video ---
        logger.info({"message": "Slicing video", "file_chunk_number": self.file_chunk_number, "filename": self.filename})
        slice_path, core_start_sec, core_end_sec, offset_sec, is_last = await self._slice_video()

        # --- Level 2: upload slice + analyze ---
        logger.info({"message": "Uploading chunk", "file_chunk_number": self.file_chunk_number, "filename": self.filename})
        video_file = await self._upload_slice(slice_path)

        logger.info({"message": "Waiting for analysis", "file_chunk_number": self.file_chunk_number, "filename": self.filename})
        seg_response, overview_response = await asyncio.gather(
            self._run_segmentation(video_file),
            self._run_overview(video_file) if self.file_chunk_number == 0 else asyncio.sleep(0),
        )

        await self._delete_file(video_file)

        # --- Parse segments ---
        raw_segments = []
        if seg_response is not None:
            raw_segments = json.loads(seg_response.text).get("segments", [])

        # --- Filter to core window + adjust timestamps to original file ---
        core_segments = self._filter_and_adjust(
            segments=raw_segments,
            overlap_sec=self.overlap_sec if self.file_chunk_number > 0 else 0.0,
            core_duration_sec=self.chunk_duration_sec,
            offset_sec=offset_sec,
        )
        logger.info(
            {
                "message": "Filtered segments",
                "file_chunk_number": self.file_chunk_number,
                "filename": self.filename,
                "num_segments": len(core_segments),
            }
        )

        # --- Guard against transcript smearing/duplication across segments ---
        core_segments = self._dedupe_transcript_across_segments(core_segments)

        logger.info(
            {
                "message": "Deduped segments",
                "file_chunk_number": self.file_chunk_number,
                "filename": self.filename,
                "num_segments": len(core_segments),
            }
        )

        # --- Level 3: build RAG chunk documents ---
        # start_index = self.rag_chunk_start_index always — index 0 is reserved
        # for the overview and is never drawn from this counter.
        segment_documents = self._build_documents(core_segments, start_index=self.rag_chunk_start_index)

        documents = segment_documents

        # --- Overview document (chunk 0 only) ---
        if self.file_chunk_number == 0 and overview_response is not None:
            overview_doc = self._build_overview_document(overview_response.text)
            documents = [overview_doc] + documents

        # next index only counts sequenced (non-overview) docs — overview's
        # fixed index 0 sits outside this counter.
        next_rag_chunk_index = self.rag_chunk_start_index + len(segment_documents)

        return documents, next_rag_chunk_index, is_last

    # -------------------------------------------------------------------------
    # Level 1 — Video slicing (async subprocess — does not block the event loop)
    # -------------------------------------------------------------------------

    async def _run_subprocess(self, cmd: List[str]) -> Tuple[bytes, bytes]:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
                f"stderr: {stderr.decode(errors='replace')}"
            )

        return stdout, stderr

    async def _get_video_duration(self, file_path: Path) -> float:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(file_path)
        ]
        stdout, _ = await self._run_subprocess(cmd)
        return float(stdout.decode().strip())

    async def _slice_video(self) -> Tuple[Path, float, float, float, bool]:
        total_sec = await self._get_video_duration(self.file_path)

        core_start_sec = self.file_chunk_number * self.chunk_duration_sec
        core_end_sec = min(core_start_sec + self.chunk_duration_sec, total_sec)

        if core_start_sec >= total_sec:
            raise ValueError(
                f"file_chunk_number={self.file_chunk_number} is out of range. "
                f"Video duration: {total_sec:.1f}s"
            )

        slice_start_sec = max(0, core_start_sec - self.overlap_sec)
        slice_end_sec = min(total_sec, core_end_sec + self.overlap_sec)
        slice_duration_sec = slice_end_sec - slice_start_sec

        is_last = core_end_sec >= total_sec

        slice_path = GEMINI_TEMP_DIR / f"{self.file_path.stem}_chunk_{self.file_chunk_number}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-ss", str(slice_start_sec),
            "-i", str(self.file_path),
            "-t", str(slice_duration_sec),
            "-c", "copy",
            str(slice_path)
        ]

        await self._run_subprocess(cmd)

        offset_sec = core_start_sec

        return (
            slice_path,
            core_start_sec,
            core_end_sec,
            offset_sec,
            is_last,
        )

    # -------------------------------------------------------------------------
    # Upload slice + wait for ACTIVE state
    # -------------------------------------------------------------------------

    async def _upload_slice(self, slice_path: Path):
        """
        Uploads the video slice to Gemini's Files API and waits for it to
        finish server-side processing (state PROCESSING -> ACTIVE).
        """
        video_file = await self._client.aio.files.upload(file=str(slice_path))
        logger.info({
            "message": "Uploaded chunk",
            "file_chunk_number": self.file_chunk_number,
            "file_name": video_file.name,
        })

        while video_file.state == "PROCESSING":
            await asyncio.sleep(self.poll_interval)
            video_file = await self._client.aio.files.get(name=video_file.name)

        if video_file.state == "FAILED":
            raise RuntimeError(
                f"Gemini file processing failed for chunk {self.file_chunk_number}: "
                f"file_name={video_file.name}"
            )

        logger.info({
            "message": "File ready",
            "file_chunk_number": self.file_chunk_number,
            "file_name": video_file.name,
        })

        return video_file

    async def _delete_file(self, video_file) -> None:
        try:
            await self._client.aio.files.delete(name=video_file.name)
        except Exception as e:
            logger.info({
                "message": "Failed to delete Gemini file (non-fatal)",
                "file_name": video_file.name,
                "error": str(e),
            })

    # -------------------------------------------------------------------------
    # Analysis calls
    # -------------------------------------------------------------------------

    async def _run_segmentation(self, video_file):
        return await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=[video_file, SEGMENT_PROMPT],
            config={
                "response_mime_type": "application/json",
                "response_schema": SEGMENT_RESPONSE_SCHEMA,
            },
        )

    async def _run_overview(self, video_file):
        return await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=[video_file, OVERVIEW_PROMPT],
        )

    # -------------------------------------------------------------------------
    # Filter overlap segments + adjust timestamps to original file
    # (identical logic to TwelveLabs processor — segments share the same shape)
    # -------------------------------------------------------------------------

    def _filter_and_adjust(
        self,
        segments: List[Dict],
        overlap_sec: float,
        core_duration_sec: float,
        offset_sec: float,
    ) -> List[Dict]:
        core_end_in_slice = overlap_sec + core_duration_sec
        result = []

        for seg in segments:
            seg_start = seg.get("start_time", 0)
            seg_end = seg.get("end_time", 0)

            if seg_start < overlap_sec:
                continue
            if seg_start >= core_end_in_slice:
                continue

            adjusted = dict(seg)
            adjusted["start_time"] = seg_start - overlap_sec + offset_sec
            adjusted["end_time"] = seg_end - overlap_sec + offset_sec

            result.append(adjusted)

        return result

    # -------------------------------------------------------------------------
    # Transcript de-duplication (guards against smearing)
    # -------------------------------------------------------------------------

    def _dedupe_transcript_across_segments(self, segments: List[Dict]) -> List[Dict]:
        result = []
        prev_transcript = ""

        for seg in segments:
            adjusted = dict(seg)
            transcript = (adjusted.get("transcript") or "").strip()

            if transcript and prev_transcript:
                if transcript == prev_transcript:
                    transcript = ""
                elif transcript in prev_transcript:
                    transcript = ""
                elif transcript.startswith(prev_transcript):
                    transcript = transcript[len(prev_transcript):].strip()

            if transcript:
                prev_transcript = (seg.get("transcript") or "").strip()

            adjusted["transcript"] = transcript
            result.append(adjusted)

        return result

    # -------------------------------------------------------------------------
    # Level 3 — Build RAG chunk Documents
    # -------------------------------------------------------------------------

    def _build_documents(self, segments: List[Dict], start_index: int) -> List[Document]:
        if not segments:
            return []

        documents = []
        current_segments: List[Dict] = []
        current_duration_sec = 0.0
        current_words = 0

        def flush() -> Optional[Document]:
            if not current_segments:
                return None

            absolute_index = start_index + len(documents)
            chunk_start = current_segments[0].get("start_time")
            chunk_end = current_segments[-1].get("end_time")

            page_content = self._render_page_content(current_segments, chunk_start, chunk_end)

            all_keywords = ", ".join(filter(None, [
                seg.get("keywords", "") for seg in current_segments
            ]))
            has_speech = any(
                (seg.get("has_speech", "false") or "false").lower() == "true"
                for seg in current_segments
            )

            return Document(
                id=f"{self.filename}-{absolute_index}",
                page_content=page_content,
                metadata={
                    "source": str(self.file_path),
                    "file_chunk_number": self.file_chunk_number,
                    "rag_chunk_number": absolute_index,
                    "provider": "gemini",
                    "model": self.model_name,
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                    "duration_sec": (
                        chunk_end - chunk_start
                        if chunk_start is not None and chunk_end is not None
                        else None
                    ),
                    "segment_count": len(current_segments),
                    "keywords": all_keywords,
                    "has_speech": has_speech,
                },
            )

        for seg in segments:
            transcript = seg.get("transcript", "") or ""
            word_count = len(transcript.split())
            duration_sec = seg.get("end_time", 0) - seg.get("start_time", 0)

            would_exceed_duration = (
                current_duration_sec + duration_sec > self.max_duration_per_rag_chunk_sec
                and current_segments
            )
            would_exceed_words = (
                current_words + word_count > self.max_words_per_rag_chunk
                and current_segments
            )

            if would_exceed_duration or would_exceed_words:
                doc = flush()
                if doc:
                    documents.append(doc)
                current_segments = []
                current_duration_sec = 0.0
                current_words = 0

            current_segments.append(seg)
            current_duration_sec += duration_sec
            current_words += word_count

        doc = flush()
        if doc:
            documents.append(doc)

        return documents

    def _render_page_content(
        self,
        segments: List[Dict],
        chunk_start: Optional[float],
        chunk_end: Optional[float],
    ) -> str:
        lines = [f"[{self._fmt_time(chunk_start)} - {self._fmt_time(chunk_end)}]"]

        def collect(field: str) -> List[str]:
            return [seg.get(field, "") for seg in segments if seg.get(field)]

        def collect_unique(field: str) -> List[str]:
            return list({seg.get(field, "") for seg in segments if seg.get(field)})

        if topics := collect("topic_summary"):
            lines.append(f"TOPIC: {' '.join(topics)}")
        if keywords := ", ".join(filter(None, collect("keywords"))):
            lines.append(f"KEYWORDS: {keywords}")
        if transcripts := collect("transcript"):
            lines.append(f"TRANSCRIPT: {' '.join(transcripts)}")
        if descriptions := collect("detailed_description"):
            lines.append(f"VISUAL: {' '.join(descriptions)}")
        if settings := collect_unique("setting"):
            lines.append(f"SETTING: {', '.join(settings)}")
        if people := collect("people_present"):
            lines.append(f"PEOPLE: {' '.join(people)}")
        if speakers := collect_unique("speaker_names"):
            lines.append(f"SPEAKERS: {', '.join(speakers)}")
        if texts := collect("on_screen_text"):
            lines.append(f"ON-SCREEN TEXT: {' '.join(texts)}")
        if audio := collect("audio_description"):
            lines.append(f"AUDIO: {' '.join(audio)}")
        if moods := collect_unique("mood"):
            lines.append(f"MOOD: {', '.join(moods)}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Overview Document (chunk 0 only)
    # -------------------------------------------------------------------------

    def _build_overview_document(self, overview_text: str) -> Document:
        return Document(
            id=f"{self.filename}-overview",
            page_content=f"VIDEO OVERVIEW\n\n{overview_text}",
            metadata={
                "source": str(self.file_path),
                "file_chunk_number": 0,
                "rag_chunk_number": 0,  # 0 is reserved for the overview only
                "provider": "gemini",
                "model": self.model_name,
                "document_type": "overview",
                "start_time": None,
                "end_time": None,
            },
        )

    @staticmethod
    def _fmt_time(seconds: Optional[float]) -> str:
        if seconds is None:
            return "--:--"
        seconds = int(seconds)
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"
