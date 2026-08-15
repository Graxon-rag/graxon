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
    # CID pattern regex for unmapped font characters from pdfminer/pdfplumber
    _CID_PATTERN = re.compile(r"\(cid\s*:\s*\d+\s*\)")

    # CJK scripts (Han, Hiragana, Katakana, Hangul) do not separate words with
    # spaces, so a geometric gap between their glyphs must not become one.
    _CJK_PATTERN = re.compile(r"[ᄀ-ᇿ぀-ヿ㄰-㆏㐀-䶿一-鿿가-힯豈-﫿]|[\U00020000-\U0002fa1f]")

    def __init__(self,
        file_path: str,
        filename: str,
        chunk_number: int,
        rag_chunk_start_index: int,
        pages_per_batch: int = Env.MAX_PAGES_PER_BATCH,
        rag_chunk_size: int = Env.CHUNK_SIZE,
        rag_chunk_overlap: int = Env.CHUNK_OVERLAP,
        # carry last N chars of previous batch to patch page boundary cuts
        tail_carry_chars: int = 500,
    ):
        self.file_path = file_path
        self.filename = filename
        self.chunk_number = chunk_number
        self.rag_chunk_start_index = rag_chunk_start_index
        self.pages_per_batch = pages_per_batch
        self.rag_chunk_size = rag_chunk_size
        self.rag_chunk_overlap = rag_chunk_overlap
        self.tail_carry_chars = tail_carry_chars

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=rag_chunk_size,
            chunk_overlap=rag_chunk_overlap,
            separators=["\n\n", "\n", ".", " ", ""],
        )

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Reads pages_per_batch pages starting from chunk_number * pages_per_batch.
        Carries tail from previous batch to avoid cutting prose at page boundaries.

        Returns:
            documents: list of Document
            next_rag_chunk_start_index: pass this to next queue message
            is_last: True if this was the final batch
        """
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

            # carry last page of previous batch to patch boundary cuts
            tail_text = ""
            if page_start > 0:
                prev_page_text = self._extract_page_text(pdf.pages[page_start - 1])
                tail_text = prev_page_text[-self.tail_carry_chars:]

            # extract text from current batch of pages
            batch_text = ""
            for page_num in range(page_start, page_end):
                batch_text += self._extract_page_text(pdf.pages[page_num])

        raw_text = tail_text + batch_text
        documents = self._split_into_rag_chunks(raw_text, page_start)

        return documents, self.rag_chunk_start_index + len(documents), is_last

    def _extract_page_text(self, page) -> str:
        """
        Extract clean text from a single pdfplumber page
        text-quality logic: filter invisible/white "color" chars,
        recover missing inter-word spaces from character geometry, and skip
        pages whose text layer is garbled (broken CID mapping or subset
        fonts silently mapping CJK glyphs to ASCII).

        Images are not processed yet -- just flagged for the future OCR pass.
        """
        if page.images:
            logger.warning(
                f"{self.filename}: page {page.page_number} contains "
                f"{len(page.images)} image(s); image content is not extracted "
                f"yet (OCR pass pending)."
            )

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

        # Strategy 1: PUA / unmapped CID characters -> genuine garbage
        sample = chars if len(chars) <= 200 else chars[:200]
        sample_text = "".join(c.get("text", "") for c in sample)
        if self._is_garbled_text(sample_text, threshold=0.3):
            logger.warning(
                f"{self.filename}: page {page.page_number} text layer looks "
                f"garbled (unmapped/PUA characters); skipping extraction for "
                f"this page (OCR pass pending)."
            )
            return ""

        # Strategy 2: font-encoding garbling -- subset fonts mapping CJK
        # glyphs onto ASCII codepoints, producing punctuation-only text
        if self._is_garbled_by_font_encoding(chars):
            logger.warning(
                f"{self.filename}: page {page.page_number} has font-encoding "
                f"garbling (subset fonts, no CJK output); skipping extraction "
                f"for this page (OCR pass pending)."
            )
            return ""

        self._insert_word_spaces(chars)
        return "".join(c["text"] for c in chars)

    def _split_into_rag_chunks(self, raw_text: str, page_start: int) -> List[Document]:
        texts = self.splitter.split_text(raw_text)

        documents = []
        for i, text in enumerate(texts):
            absolute_index = self.rag_chunk_start_index + i
            doc = Document(
                id=f"{self.filename}-{absolute_index}",
                page_content=text,
                metadata={
                    "source": self.file_path,
                    "file_chunk_number": self.chunk_number,
                    "rag_chunk_number": absolute_index,
                    "page_number": page_start,       # which page batch this came from
                },
            )
            documents.append(doc)

        return documents

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
        """Recover missing spaces from character geometry (mutates in place)."""
        widths = [c["width"] for c in chars if c["text"] and c["text"].strip()]
        mean_w = sum(widths) / len(widths) if widths else 0
        if mean_w <= 0:
            return
        for cur, nxt in zip(chars, chars[1:]):
            if (
                cur["text"] and nxt["text"]
                and cur["text"].strip() and nxt["text"].strip()
                and not cls._CJK_PATTERN.search(cur["text"])
                and not cls._CJK_PATTERN.search(nxt["text"])
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
