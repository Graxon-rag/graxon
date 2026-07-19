from .model import Utterance, Transcript, Word
from langchain_core.documents import Document
from typing import List, Optional

# ---------------------------------------------------------------------------
# Speaker block — a group of consecutive utterances from the same speaker
# ---------------------------------------------------------------------------


class SpeakerBlock:
    """
    Accumulates consecutive utterances from the same speaker.
    Rendered as a single labelled block in page_content:

        [Speaker A | 00:02 - 00:47]        ← with diarization
        text line 1
        text line 2

        [00:02 - 00:47]                     ← without diarization (Groq)
        text line 1
    """

    def __init__(self, speaker: Optional[str], has_diarization: bool):
        self.speaker = speaker
        self.has_diarization = has_diarization
        self.lines: List[str] = []
        self.start: Optional[float] = None
        self.end: Optional[float] = None

    def add(self, utterance: Utterance) -> None:
        if self.start is None:
            self.start = utterance.start
        self.end = utterance.end
        self.lines.append(utterance.text.strip())

    def render(self) -> str:
        """Renders the block as a string for page_content."""
        header = self._header()
        body = "\n".join(self.lines)
        return f"{header}\n{body}"

    def _header(self) -> str:
        time_range = f"{fmt_time(self.start)} - {fmt_time(self.end)}"
        if self.has_diarization and self.speaker:
            # Normalize: "speaker_0" → "0", "A" → "A", "0" → "0"
            label = self.speaker.replace("speaker_", "").replace("Speaker_", "")
            return f"[Speaker {label} | {time_range}]"
        return f"[{time_range}]"


def build_documents(
    transcript: Transcript,
    filename: str,
    file_chunk_number: int,
    rag_chunk_start_index: int,
    max_time_per_rag_chunk_ms: float,
    max_words_per_rag_chunk: int,
    has_diarization: bool,              # False for Groq/Whisper, True for all others
    source_file: str,
) -> List[Document]:
    """
    Converts a normalized Transcript into a list of LangChain Documents.

    Two-level grouping:
      Level 1 — RAG chunk guards (whichever fires first stops the chunk):
                  accumulated duration >= max_time_per_rag_chunk_ms
                  accumulated word count >= max_words_per_rag_chunk
      Level 2 — Speaker merging within each RAG chunk:
                  consecutive utterances from the same speaker → one SpeakerBlock
                  one header per block instead of one header per utterance
                  this keeps embeddings clean — content dominates over formatting

    Guard priority: RAG guards fire first, speaker merging happens within the chunk.
    So if Speaker A talks for 5 minutes, it still splits into multiple RAG chunks.
    """
    if not transcript.utterances:
        return []

    documents: List[Document] = []

    # Current RAG chunk state
    current_utterances: List[Utterance] = []
    current_words: int = 0
    current_duration_ms: float = 0.0

    def flush() -> Optional[Document]:
        """Flush current_utterances into one Document with merged speaker blocks."""
        if not current_utterances:
            return None

        absolute_index = rag_chunk_start_index + len(documents)

        # --- Speaker merging ---
        # Group consecutive same-speaker utterances into SpeakerBlocks
        blocks: List[SpeakerBlock] = []
        current_block: Optional[SpeakerBlock] = None

        for u in current_utterances:
            if current_block is None or u.speaker != current_block.speaker:
                # New speaker (or first utterance) — start a new block
                current_block = SpeakerBlock(
                    speaker=u.speaker,
                    has_diarization=has_diarization,
                )
                blocks.append(current_block)
            current_block.add(u)

        # Render blocks — blank line between blocks for readability
        page_content = "\n\n".join(block.render() for block in blocks)

        # Chunk time range
        chunk_start = current_utterances[0].start
        chunk_end = current_utterances[-1].end

        return Document(
            id=f"{filename}-{absolute_index}",
            page_content=page_content,
            metadata={
                "source": source_file,
                "file_chunk_number": file_chunk_number,
                "rag_chunk_number": absolute_index,
                "provider": transcript.provider,
                "language": transcript.language,
                "start_time": round(chunk_start, 2) if chunk_start is not None else None,  # max 2 decimal places
                "end_time": round(chunk_end, 2) if chunk_end is not None else None,
                "duration_sec": (
                    round(chunk_end - chunk_start, 2)
                    if chunk_start is not None and chunk_end is not None
                    else None
                ),
                "utterance_count": len(current_utterances),
                "speaker_block_count": len(blocks),
                "speakers": (
                    list({u.speaker for u in current_utterances if u.speaker})
                    if has_diarization else []
                ),
            },
        )

    for utterance in transcript.utterances:
        word_count = len(utterance.text.split())
        duration_ms = (
            (utterance.end - utterance.start) * 1000
            if utterance.start is not None and utterance.end is not None
            else 0.0
        )

        # --- RAG guards (priority over speaker merging) ---
        would_exceed_time = (
            current_duration_ms + duration_ms > max_time_per_rag_chunk_ms
            and current_utterances   # always include at least one utterance
        )
        would_exceed_words = (
            current_words + word_count > max_words_per_rag_chunk
            and current_utterances
        )

        if would_exceed_time or would_exceed_words:
            doc = flush()
            if doc:
                documents.append(doc)
            current_utterances = []
            current_words = 0
            current_duration_ms = 0.0

        current_utterances.append(utterance)
        current_words += word_count
        current_duration_ms += duration_ms

    # Flush final group
    doc = flush()
    if doc:
        documents.append(doc)

    return documents


def fmt_time(seconds: Optional[float]) -> str:
    """Formats seconds as MM:SS or HH:MM:SS."""
    if seconds is None:
        return "--:--"
    seconds = int(seconds)
    h, remainder = divmod(seconds, 3600)
    m, s = divmod(remainder, 60)
    return f"{h:02}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}"
