from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.utils.logger import logger
from .processor import Processor
from app.config.env import Env
from typing import List, Tuple
import unicodedata
import pdfplumber
import asyncio
import re


class PDFProcessor(Processor):
    _CID_PATTERN = re.compile(r"\(cid\s*:\s*\d+\s*\)")

    def __init__(self,
        file_path: str,
        filename: str,
        chunk_number: int,
        rag_chunk_start_index: int,
        pages_per_batch: int = Env.MAX_PAGES_PER_BATCH,
        rag_chunk_size: int = Env.CHUNK_SIZE,
        rag_chunk_overlap: int = Env.CHUNK_OVERLAP,
        tail_carry_chars: int = 500,
        # tables larger than this get split by the normal splitter too,
        # instead of being force-kept as one giant chunk
        max_table_chunk_chars: int = 4000,
    ):
        self.file_path = file_path
        self.filename = filename
        self.chunk_number = chunk_number
        self.rag_chunk_start_index = rag_chunk_start_index
        self.pages_per_batch = pages_per_batch
        self.rag_chunk_size = rag_chunk_size
        self.rag_chunk_overlap = rag_chunk_overlap
        self.tail_carry_chars = tail_carry_chars
        self.max_table_chunk_chars = max_table_chunk_chars

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_chunk_size,
            chunk_overlap=rag_chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
        )
        # only used for oversized tables, keep row boundaries intact
        self.table_splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_chunk_size,
            chunk_overlap=0,
            separators=["\n", " ", ""],
        )

    async def process(self) -> Tuple[List[Document], int, bool]:
        try:
            return await asyncio.to_thread(self._process_sync)
        except Exception as e:
            logger.error(f"Failed to process PDF file {self.file_path}. Error: {e}")
            raise e

    def _process_sync(self) -> Tuple[List[Document], int, bool]:
        with pdfplumber.open(self.file_path) as pdf:
            total_pages = len(pdf.pages)

            page_start = self.chunk_number * self.pages_per_batch
            if page_start >= total_pages:
                raise ValueError(
                    f"chunk_number {self.chunk_number} is out of range. "
                    f"Total pages: {total_pages}, pages_per_batch: {self.pages_per_batch}"
                )

            page_end = min(page_start + self.pages_per_batch, total_pages)
            is_last = page_end >= total_pages

            tail_text = ""
            if page_start > 0:
                prev_text, _ = self._extract_page(pdf.pages[page_start - 1])
                tail_text = prev_text[-self.tail_carry_chars:]

            batch_text = ""
            batch_tables: List[Tuple[int, str]] = []  # (page_number, markdown)
            for page_num in range(page_start, page_end):
                page_text, page_tables = self._extract_page(pdf.pages[page_num])
                batch_text += page_text
                for md in page_tables:
                    batch_tables.append((page_num, md))

        raw_text = tail_text + batch_text
        documents = self._build_documents(raw_text, batch_tables, page_start)

        return documents, self.rag_chunk_start_index + len(documents), is_last

    def _extract_page(self, page) -> Tuple[str, List[str]]:
        """
        Returns (prose_text, table_markdowns) for a single page.
        Table regions are excluded from prose_text so content isn't
        duplicated/garbled by the char-level text extraction.
        """
        if page.images:
            logger.warning(
                f"{self.filename}: page {page.page_number} contains "
                f"{len(page.images)} image(s); image content is not extracted "
                f"yet (OCR pass pending)."
            )

        table_mds: List[str] = []
        table_bboxes = []
        try:
            found_tables = page.find_tables()
        except Exception as e:
            logger.warning(
                f"{self.filename}: table detection failed on page "
                f"{page.page_number}: {e}"
            )
            found_tables = []

        for t in found_tables:
            try:
                rows = t.extract()
            except Exception as e:
                logger.warning(
                    f"{self.filename}: failed to extract a table on page "
                    f"{page.page_number}: {e}"
                )
                continue
            md = self._table_to_markdown(rows)
            if md:
                table_mds.append(md)
                table_bboxes.append(t.bbox)  # (x0, top, x1, bottom)

        prose_text = self._extract_prose_text(page, table_bboxes)
        return prose_text, table_mds

    def _extract_prose_text(self, page, table_bboxes) -> str:
        try:
            chars = [c for c in page.dedupe_chars().chars if self._has_color(c)]
        except Exception as e:
            logger.warning(
                f"{self.filename}: failed to extract characters on page "
                f"{page.page_number}: {e}"
            )
            return ""

        if not chars:
            return ""

        # drop chars that fall inside a detected table's bbox so table
        # content isn't duplicated (once as markdown, once as raw prose)
        if table_bboxes:
            chars = [c for c in chars if not self._in_any_bbox(c, table_bboxes)]
            if not chars:
                return ""

        sample = chars if len(chars) <= 200 else chars[:200]
        sample_text = "".join(c.get("text", "") for c in sample)
        if self._is_garbled_text(sample_text, threshold=0.3):
            logger.warning(
                f"{self.filename}: page {page.page_number} text layer looks "
                f"garbled; skipping extraction for this page (OCR pass pending)."
            )
            return ""

        if self._is_garbled_by_font_encoding(chars):
            logger.warning(
                f"{self.filename}: page {page.page_number} has font-encoding "
                f"garbling; skipping extraction for this page (OCR pass pending)."
            )
            return ""

        self._insert_word_spaces(chars)
        return "".join(c["text"] for c in chars)

    @staticmethod
    def _in_any_bbox(c, bboxes) -> bool:
        cx0, ctop, cx1, cbottom = c["x0"], c["top"], c["x1"], c["bottom"]
        for (x0, top, x1, bottom) in bboxes:
            if cx0 >= x0 - 1 and cx1 <= x1 + 1 and ctop >= top - 1 and cbottom <= bottom + 1:
                return True
        return False

    @staticmethod
    def _table_to_markdown(rows: List[List]) -> str:
        """Convert pdfplumber's raw row/cell extraction into a markdown table."""
        # drop fully-empty rows
        rows = [r for r in rows if any((cell or "").strip() for cell in r)]
        if not rows:
            return ""

        def clean(cell):
            return re.sub(r"\s+", " ", (cell or "").strip()).replace("|", "\\|")

        header, *body = rows
        header_cells = [clean(c) for c in header]
        col_count = len(header_cells)

        lines = [
            "| " + " | ".join(header_cells) + " |",
            "| " + " | ".join(["---"] * col_count) + " |",
        ]
        for row in body:
            cells = [clean(c) for c in row]
            # pad/truncate ragged rows to header width
            if len(cells) < col_count:
                cells += [""] * (col_count - len(cells))
            elif len(cells) > col_count:
                cells = cells[:col_count]
            lines.append("| " + " | ".join(cells) + " |")

        return "\n".join(lines)

    def _build_documents(
        self, raw_text: str, batch_tables: List[Tuple[int, str]], page_start: int
    ) -> List[Document]:
        documents: List[Document] = []

        # 1. prose text -> normal recursive-split chunks
        texts = self.splitter.split_text(raw_text)
        for text in texts:
            documents.append(self._make_document(text, page_start, is_table=False))

        # 2. tables -> atomic chunks (own chunk each), split only if oversized
        for page_num, md in batch_tables:
            if len(md) <= self.max_table_chunk_chars:
                documents.append(
                    self._make_document(md, page_num, is_table=True)
                )
            else:
                logger.warning(
                    f"{self.filename}: table on page {page_num + 1} exceeds "
                    f"{self.max_table_chunk_chars} chars, splitting it."
                )
                for part in self.table_splitter.split_text(md):
                    documents.append(
                        self._make_document(part, page_num, is_table=True)
                    )

        # re-stamp sequential absolute indices / ids now that final order is known
        for i, doc in enumerate(documents):
            absolute_index = self.rag_chunk_start_index + i
            doc.id = f"{self.filename}-{absolute_index}"
            doc.metadata["rag_chunk_number"] = absolute_index

        return documents

    def _make_document(self, text: str, page_number: int, is_table: bool) -> Document:
        return Document(
            id="",  # stamped in _build_documents
            page_content=text,
            metadata={
                "source": self.file_path,
                "file_chunk_number": self.chunk_number,
                "rag_chunk_number": -1,  # stamped in _build_documents
                "page_number": page_number,
                "content_type": "table" if is_table else "text",
            },
        )

    @staticmethod
    def _has_color(o):
        if o.get("ncs", "") == "DeviceGray":
            if (
                o.get("stroking_color") and o["stroking_color"][0] == 1
                and o.get("non_stroking_color") and o["non_stroking_color"][0] == 1
            ):
                if re.match(r"[a-zT_\[\]\(\)-]+", o.get("text", "")):
                    return False
        return True

    @classmethod
    def _insert_word_spaces(cls, chars, gap_ratio=0.25):
        widths = [c["width"] for c in chars if c["text"] and c["text"].strip()]
        mean_w = sum(widths) / len(widths) if widths else 0
        if mean_w <= 0:
            return
        for cur, nxt in zip(chars, chars[1:]):
            if (
                cur["text"] and nxt["text"]
                and cur["text"].strip() and nxt["text"].strip()
                and nxt["x0"] - cur["x1"] > mean_w * gap_ratio
            ):
                cur["text"] += " "

    @staticmethod
    def _is_garbled_char(ch):
        if not ch:
            return False
        cp = ord(ch)
        if 0xE000 <= cp <= 0xF8FF:
            return True
        if 0xF0000 <= cp <= 0xFFFFF:
            return True
        if 0x100000 <= cp <= 0x10FFFF:
            return True
        if cp == 0xFFFD:
            return True
        if cp < 0x20 and ch not in ("\t", "\n", "\r"):
            return True
        if 0x80 <= cp <= 0x9F:
            return True
        return unicodedata.category(ch) in ("Cn", "Cs")

    @classmethod
    def _is_garbled_text(cls, text, threshold=0.5):
        if not text or not text.strip():
            return False
        if cls._CID_PATTERN.search(text):
            return True
        garbled_count = 0
        total = 0
        for ch in text:
            if ch.isspace():
                continue
            total += 1
            if cls._is_garbled_char(ch):
                garbled_count += 1
        if total == 0:
            return False
        return garbled_count / total >= threshold

    @staticmethod
    def _has_subset_font_prefix(fontname):
        if not fontname:
            return False
        return bool(re.match(r"^[A-Z0-9]{2,6}\+", fontname))

    @classmethod
    def _is_garbled_by_font_encoding(cls, page_chars, min_chars=20):
        if not page_chars or len(page_chars) < min_chars:
            return False

        subset_font_count = 0
        total_non_space = 0
        ascii_punct_sym = 0
        cjk_like = 0

        for c in page_chars:
            text = c.get("text", "")
            fontname = c.get("fontname", "")
            if not text or text.isspace():
                continue
            total_non_space += 1

            if cls._has_subset_font_prefix(fontname):
                subset_font_count += 1

            cp = ord(text[0])
            if (
                0x2E80 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF
                or 0x20000 <= cp <= 0x2FA1F or 0xAC00 <= cp <= 0xD7AF
                or 0x3040 <= cp <= 0x30FF
            ):
                cjk_like += 1
            elif 0x21 <= cp <= 0x2F or 0x3A <= cp <= 0x40 or 0x5B <= cp <= 0x60 or 0x7B <= cp <= 0x7E:
                ascii_punct_sym += 1

        if total_non_space < min_chars:
            return False

        subset_ratio = subset_font_count / total_non_space
        if subset_ratio < 0.3:
            return False

        cjk_ratio = cjk_like / total_non_space
        punct_ratio = ascii_punct_sym / total_non_space
        return cjk_ratio < 0.05 and punct_ratio > 0.4
