from langchain_text_splitters import MarkdownTextSplitter
from langchain_core.documents import Document
from app.utils.logger import logger
from .processor import Processor
from app.config.env import Env
from typing import List, Tuple
import aiofiles
import chardet
import os


class MarkdownProcessor(Processor):
    def __init__(self,
        file_path: str,
        filename: str,
        chunk_number: int,
        rag_chunk_start_index: int,
        max_chunk_size_mb: float = 50,
        rag_chunk_size: int = Env.CHUNK_SIZE,
        rag_chunk_overlap: int = Env.CHUNK_OVERLAP,
        tail_carry_chars: int = 500,
    ):
        self.file_path = file_path
        self.filename = filename
        self.chunk_number = chunk_number
        self.rag_chunk_start_index = rag_chunk_start_index
        self.max_chunk_size_mb = max_chunk_size_mb
        self.rag_chunk_size = rag_chunk_size
        self.rag_chunk_overlap = rag_chunk_overlap
        self.tail_carry_chars = tail_carry_chars

        self.io_buffer_size = int(max_chunk_size_mb * 1024 * 1024)  # bytes

        # MarkdownTextSplitter respects markdown structure:
        # tries to split on headers (##, ###) first, then paragraphs, then sentences
        self.splitter = MarkdownTextSplitter(
            chunk_size=rag_chunk_size,
            chunk_overlap=rag_chunk_overlap,
        )

    def _get_io_buffer_offset(self) -> int:
        """Calculate byte offset for the requested chunk_number."""
        return self.chunk_number * self.io_buffer_size

    def _detect_encoding(self) -> str:
        with open(self.file_path, "rb") as f:
            raw = f.read(10000)  # sample first 10KB, enough to detect
        result = chardet.detect(raw)
        return result["encoding"] or "utf-8"

    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Reads only the requested IO buffer (chunk_number * max_chunk_size_mb),
        carries tail from previous buffer to handle boundary cuts,
        then splits into semantic RAG chunks.

        Returns:
            documents: list of Document
            next_rag_chunk_start_index: pass this to next queue message
            is_last: True if this was the final IO chunk
        """
        try:
            offset = self._get_io_buffer_offset()
            file_size = os.path.getsize(self.file_path)

            if offset >= file_size:
                raise ValueError(
                    f"chunk_number {self.chunk_number} is out of range. "
                    f"File size: {file_size} bytes, max_chunk_size_mb: {self.max_chunk_size_mb}MB"
                )

            raw_text = await self._read_buffer_at_offset(offset)
            documents = self._split_into_rag_chunks(raw_text, offset)

            is_last = (offset + self.io_buffer_size) >= file_size
            return documents, self.rag_chunk_start_index + len(documents), is_last

        except Exception as e:
            logger.error(f"Failed to process markdown file {self.file_path}. Error: {e}")
            raise e

    async def _read_buffer_at_offset(self, offset: int) -> str:
        """
        Reads one IO buffer from disk at the given offset.
        Also reads tail_carry_chars from the previous buffer
        to avoid cutting sentences at the IO boundary.
        """
        tail_start = max(0, offset - self.tail_carry_chars)
        tail_length = offset - tail_start  # 0 if first chunk

        encoding = self._detect_encoding()
        async with aiofiles.open(self.file_path, "r", encoding=encoding, errors="replace") as f:
            if tail_length > 0:
                await f.seek(tail_start)
                tail_text = await f.read(tail_length)
            else:
                tail_text = ""

            await f.seek(offset)
            buffer_text = await f.read(self.io_buffer_size)

        return tail_text + buffer_text

    def _split_into_rag_chunks(self, raw_text: str, offset: int) -> List[Document]:
        """
        Splits raw IO buffer text into semantic RAG chunks using MarkdownTextSplitter.
        Each chunk is wrapped in a Document with metadata.
        """
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
                    "byte_offset": offset,
                },
            )
            documents.append(doc)

        return documents
