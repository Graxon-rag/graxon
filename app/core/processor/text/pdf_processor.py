from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.utils.logger import logger
from .processor import Processor
from app.config.env import Env
from typing import List, Tuple
import fitz  # pymupdf
import os


class PDFProcessor(Processor):
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
            doc = fitz.open(self.file_path)
            total_pages = len(doc)

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
                prev_page_text = doc[page_start - 1].get_text()
                tail_text = prev_page_text[-self.tail_carry_chars:]

            # extract text from current batch of pages
            batch_text = ""
            for page_num in range(page_start, page_end):
                page_text = doc[page_num].get_text()
                batch_text += page_text

            doc.close()

            raw_text = tail_text + batch_text
            documents = self._split_into_rag_chunks(raw_text, page_start)

            return documents, self.rag_chunk_start_index + len(documents), is_last

        except Exception as e:
            logger.error(f"Failed to process PDF file {self.file_path}. Error: {e}")
            raise e

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
