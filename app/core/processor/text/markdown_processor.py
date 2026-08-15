from chonkie import Chunk, MarkdownChef, SentenceChunker
from langchain_core.documents import Document
from app.config.config import Config
from app.utils.logger import logger
from .processor import Processor
from typing import List, Tuple
from app.config.env import Env
from pathlib import Path
import json
import re


FRAGMENT_ROW_THRESHOLD = 3  # tables with <= this many data rows are "fragments"
TEXT_CHUNK_SIZE = 1000  # characters per text sub-chunk
TEXT_CHUNK_OVERLAP = 100  # character overlap between consecutive text sub-chunks

HEADING_RE = re.compile(r"^#{1,6}\s+.*$", re.MULTILINE)
DATA_VALUE_RE = re.compile(r"^\(?-?\$?\s*-?[\d,]+(\.\d+)?%?\)?$")

DEBUG_FOLDER = "debug"


class MarkdownProcessor(Processor):
    """
    Two-stage, queue-friendly wrapper around chonkie's MarkdownChef.

    WHY TWO STAGES:
    MarkdownChef needs the WHOLE document to correctly detect table boundaries
    and to walk backward for the nearest heading. Unlike raw-text windowing
    (byte offset + tail_carry_chars), a markdown table can't be split across
    an IO buffer boundary and still parse correctly. So parsing itself cannot
    be chunk_number-windowed the way MarkdownProcessor windows raw reads.

    Stage 1 (runs once per file, whichever message arrives first and finds
    no cache):
        Parses the ENTIRE file with MarkdownChef, builds the full ordered
        chunk list exactly as before (tables -> sentences, text -> sentence
        chunks, sequenced by document position), and caches it to disk as
        JSON next to the source file.

    Stage 2 (runs on every message, including the first):
        Reads back ONE PAGE from the cache, sized to ~max_chunk_size_mb (like
        MarkdownProcessor's IO buffer), and returns
        (chunks, next_chunk_number, is_last) -- the same contract your
        RabbitMQ consumer already uses with MarkdownProcessor, so you can
        drop this into the same "read result -> enqueue next chunk_number"
        loop.

        Page boundaries are chunk-aligned AND table-aware: a page never cuts
        a table's rows in half. If growing the page to include the rest of a
        table would put it over max_chunk_size_mb, it's allowed to -- the
        alternative (a truncated table) is worse.

    NOTE ON CONCURRENCY: if two consumers can pick up chunk_number=0 for the
    same file at once, they'll race to write the cache. Either make your
    producer emit a single "parse" message before fanning out page messages,
    or add a file lock / atomic rename when writing the cache below.
    """

    def __init__(
        self,
        markdown_path: str,
        filename: str,
        chunk_number: int,
        rag_chunk_start_index: int,
        max_chunk_size_mb: float = Env.MAX_CHUNK_SIZE_MB,
        tokenizer: str = "gpt2",
        cache_dir: str | None = None,
    ):
        self.markdown_path = markdown_path
        self.filename = filename
        self.chunk_number = chunk_number
        self.rag_chunk_start_index = rag_chunk_start_index
        self.max_page_bytes = int(max_chunk_size_mb * 1024 * 1024)
        self.chef = MarkdownChef(tokenizer)

        cache_dir = Path(cache_dir) if cache_dir else Path(markdown_path).parent  # type: ignore
        self.cache_path = cache_dir / f"{Path(markdown_path).stem}.chunks.json"  # type: ignore

    async def process(self) -> Tuple[List[Document], int, bool]:
        try:
            needs_rebuild = self.chunk_number == 0 or not self.cache_path.exists()

            if needs_rebuild:
                logger.info(
                    "Parsing (first page of file, or cache missing)",
                    extra={"markdown_path": self.markdown_path},
                )
                self._parse_and_cache()

            all_chunks = self._load_cache()
            total = len(all_chunks)

            pages = self._compute_pages(all_chunks)
            if self.chunk_number >= len(pages):
                raise ValueError(
                    f"chunk_number {self.chunk_number} is out of range. "
                    f"{len(pages)} total pages for {total} chunks."
                )

            start, end = pages[self.chunk_number]
            page = all_chunks[start:end]
            is_last = self.chunk_number == len(pages) - 1

            for c in page:
                c.metadata["file_chunk_number"] = self.chunk_number
                c.metadata["filename"] = self.filename

            if is_last:
                if Config.is_dev_env() or Config.is_test_env():
                    logger.info(f"Writing {total} chunks to {DEBUG_FOLDER}", extra={"markdown_path": self.markdown_path})
                    self._write_debug_markdown(all_chunks, path=f"{DEBUG_FOLDER}/{Path(self.markdown_path).stem}.md")
                self.cache_path.unlink(missing_ok=True)

            documents = [
                Document(
                    id=f"{self.filename}-{c.metadata.get('rag_chunk_number')}",
                    page_content=c.text,
                    metadata=c.metadata,
                )
                for c in page
            ]

            return documents, self.rag_chunk_start_index + len(page), is_last

        except Exception:
            logger.exception(f"Failed to process markdown: {self.markdown_path}")
            raise

    # ------------------------------------------------------------------ #
    # Stage 1: full-document parse + cache
    # ------------------------------------------------------------------ #

    def _parse_and_cache(self) -> None:
        doc = self.chef.process(self.markdown_path)

        logger.info(f"Found {len(doc.tables)} tables", extra={"markdown_path": self.markdown_path})
        logger.info(f"Found {len(doc.code)} code blocks", extra={"markdown_path": self.markdown_path})
        logger.info(f"Found {len(doc.images)} images", extra={"markdown_path": self.markdown_path})
        logger.info(f"Found {len(doc.chunks)} text chunks", extra={"markdown_path": self.markdown_path})

        table_chunks = self._build_table_chunks(doc, source_file=self.markdown_path)
        text_chunks = self._build_text_chunks(doc, source_file=self.markdown_path)

        all_chunks = self._assign_sequence(table_chunks + text_chunks)

        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.cache_path.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump([self._chunk_to_dict(c) for c in all_chunks], f)
        tmp_path.replace(self.cache_path)

    def _chunk_to_dict(self, c: Chunk) -> dict:
        return {
            "text": c.text,
            "start_index": c.start_index,
            "end_index": c.end_index,
            "metadata": c.metadata,
        }

    def _load_cache(self) -> List[Chunk]:
        with open(self.cache_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [
            Chunk(text=r["text"], start_index=r["start_index"], end_index=r["end_index"], metadata=r["metadata"])
            for r in raw
        ]

    def _compute_pages(self, all_chunks: List[Chunk]) -> List[Tuple[int, int]]:
        """
        Groups chunks into pages of ~max_page_bytes each, WITHOUT ever cutting a
        page boundary in the middle of the same table's rows.

        A table becomes multiple consecutive "table_row" chunks sharing the same
        table_index. If a page would normally end in the middle of one of those
        runs, we keep pulling in rows until that table finishes -- even if the
        page ends up a bit larger than max_page_bytes. Fragment/unparsed tables
        are already single chunks, so they can never be split regardless.

        Returns a list of (start, end) index ranges into all_chunks, one per
        page/chunk_number.
        """
        pages: List[Tuple[int, int]] = []
        page_start = 0
        page_bytes = 0

        for i, c in enumerate(all_chunks):
            c_bytes = len(c.text.encode("utf-8"))

            if page_bytes > 0 and page_bytes + c_bytes > self.max_page_bytes:
                prev = all_chunks[i - 1]
                mid_table = (
                    c.metadata.get("kind") == "table_row"
                    and prev.metadata.get("kind") == "table_row"
                    and c.metadata.get("table_index") == prev.metadata.get("table_index")
                )
                if not mid_table:
                    pages.append((page_start, i))
                    page_start = i
                    page_bytes = 0

            page_bytes += c_bytes

        pages.append((page_start, len(all_chunks)))
        return pages

    def _find_preceding_text(self, table_start: int, text_chunks: list[Chunk], max_context_chars: int = 400) -> str:
        """Return the tail of the closest text chunk that ends before this table starts."""
        candidates = [c for c in text_chunks if c.end_index <= table_start]
        if not candidates:
            return ""
        closest = max(candidates, key=lambda c: c.end_index)
        text = closest.text.strip()
        return text[-max_context_chars:] if len(text) > max_context_chars else text

    def _last_heading(self, text: str) -> str:
        """Grab the last markdown heading line in a block of text, if any."""
        headings = HEADING_RE.findall(text)
        if not headings:
            return ""
        return headings[-1].lstrip("#").strip().strip("*")

    def _find_last_heading_before(self, position: int, text_chunks: list[Chunk]) -> str:
        """Scan backward through raw text chunks (full text, not truncated) to find
        the closest preceding markdown heading."""
        candidates = sorted(
            (c for c in text_chunks if c.start_index < position),
            key=lambda c: c.start_index,
        )
        for c in reversed(candidates):
            h = self._last_heading(c.text)
            if h:
                return h
        return ""

    def _looks_like_data_value(self, cell: str) -> bool:
        """True if a cell looks like a number/currency/percentage rather than a
        column label."""
        return bool(DATA_VALUE_RE.match(cell.strip()))

    def _parse_markdown_table(self, table_md: str) -> tuple[list[str], list[list[str]], bool]:
        """Very small markdown-table parser: returns (headers, rows, has_header)."""
        lines = [ln for ln in table_md.strip().splitlines() if ln.strip().startswith("|")]
        if not lines:
            return [], [], False

        def split_row(line: str) -> list[str]:
            cells = line.strip().strip("|").split("|")
            return [c.strip().strip("*_") for c in cells]

        has_separator = len(lines) >= 2 and bool(re.match(r"^\|?[\s:-]+\|", lines[1]))

        headers: list[str] = []
        body_lines = lines

        if has_separator:
            candidate_headers = split_row(lines[0])
            non_empty = sum(1 for h in candidate_headers[1:] if h)
            looks_fake = (
                any(self._looks_like_data_value(h) for h in candidate_headers[1:])
                or non_empty == 0
            )
            if looks_fake:
                body_lines = [lines[0]] + lines[2:]
            else:
                headers = candidate_headers
                body_lines = lines[2:]

        rows = [split_row(ln) for ln in body_lines]
        return headers, rows, bool(headers)

    def _rows_to_sentences(self, headers: list[str], rows: list[list[str]], title: str) -> list[str]:
        """Turn each table row into one natural-language sentence with the title baked in."""
        sentences = []
        for row in rows:
            if not any(cell for cell in row):
                continue
            label = row[0] if row[0] else "Row"

            if headers:
                parts = [
                    f"{headers[i]}: {row[i]}"
                    for i in range(1, len(row))
                    if i < len(headers) and headers[i] and row[i]
                ]
            else:
                parts = [cell for cell in row[1:] if cell]

            if not parts:
                continue
            prefix = f"{title} — " if title else ""
            sentences.append(f"{prefix}{label}: " + ", ".join(parts))
        return sentences

    def _count_data_rows(self, table_md: str) -> int:
        _headers, rows, _has_header = self._parse_markdown_table(table_md)
        return len(rows)

    def _build_table_chunks(self, doc, source_file: str) -> list[Chunk]:
        """Build one Chunk per table row (or merged-fragment chunk)."""
        table_chunks: list[Chunk] = []

        for t_idx, table in enumerate(doc.tables):
            context = self._find_preceding_text(table.start_index, doc.chunks)
            title = self._find_last_heading_before(table.start_index, doc.chunks) or context[:120].strip()

            n_rows = self._count_data_rows(table.content)

            if n_rows <= FRAGMENT_ROW_THRESHOLD:
                merged_text = f"{context}\n{table.content}".strip()
                table_chunks.append(
                    Chunk(
                        text=merged_text,
                        start_index=table.start_index,
                        end_index=table.end_index,
                        metadata={
                            "source": source_file,
                            "byte_offset": table.start_index,
                            "table_index": t_idx,
                            "title": title,
                            "kind": "fragment_table",
                        },
                    )
                )
                continue

            headers, rows, _has_header = self._parse_markdown_table(table.content)
            sentences = self._rows_to_sentences(headers, rows, title)

            if not sentences:
                merged_text = f"{context}\n{table.content}".strip()
                table_chunks.append(
                    Chunk(
                        text=merged_text,
                        start_index=table.start_index,
                        end_index=table.end_index,
                        metadata={
                            "source": source_file,
                            "byte_offset": table.start_index,
                            "table_index": t_idx,
                            "title": title,
                            "kind": "unparsed_table",
                        },
                    )
                )
                continue

            for r_idx, sentence in enumerate(sentences):
                table_chunks.append(
                    Chunk(
                        text=sentence,
                        start_index=table.start_index,
                        end_index=table.end_index,
                        metadata={
                            "source": source_file,
                            "byte_offset": table.start_index,
                            "table_index": t_idx,
                            "row_index": r_idx,
                            "title": title,
                            "kind": "table_row",
                        },
                    )
                )

        return table_chunks

    def _build_text_chunks(self, doc, source_file: str) -> list[Chunk]:
        """Re-chunk doc.chunks into ~TEXT_CHUNK_SIZE pieces using chonkie's
        SentenceChunker, with the nearest heading prepended for context."""
        sentence_chunker = SentenceChunker(
            tokenizer="character",
            chunk_size=TEXT_CHUNK_SIZE,
            chunk_overlap=TEXT_CHUNK_OVERLAP,
        )

        text_chunks: list[Chunk] = []

        for raw_chunk in doc.chunks:
            if not raw_chunk.text.strip():
                continue

            sub_chunks = sentence_chunker.chunk(raw_chunk.text)
            offset = raw_chunk.start_index

            for sub in sub_chunks:
                global_start = offset + sub.start_index
                global_end = offset + sub.end_index

                title = self._last_heading(sub.text)
                if not title:
                    title = self._find_last_heading_before(global_start, doc.chunks)

                text = f"{title}\n{sub.text}".strip() if title and title not in sub.text else sub.text

                text_chunks.append(
                    Chunk(
                        text=text,
                        start_index=global_start,
                        end_index=global_end,
                        metadata={
                            "source": source_file,
                            "byte_offset": global_start,
                            "title": title,
                            "kind": "text",
                        },
                    )
                )

        return text_chunks

    def _assign_sequence(self, chunks: list[Chunk]) -> list[Chunk]:
        """Sort all chunks by document position and stamp each with its absolute
        rag_chunk_number, starting from self.rag_chunk_start_index (passed in at
        object creation, same as MarkdownProcessor). This lets a caller continue
        the numbering on from wherever a previous run/file left off, instead of
        always restarting at 0. This is the semantic chunk index across the
        whole file, independent of the queue-level page chunk_number, which
        process() stamps separately as file_chunk_number when a page is read
        out."""
        ordered = sorted(chunks, key=lambda c: c.start_index)
        for i, c in enumerate(ordered):
            c.metadata["rag_chunk_number"] = self.rag_chunk_start_index + i
        return ordered

    def _write_debug_markdown(self, chunks: list[Chunk], path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for c in chunks:
                f.write(f"<!-- {c.metadata} -->\n{c.text}\n\n---\n\n")
