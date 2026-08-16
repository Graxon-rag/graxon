from langchain_core.documents import Document
from ..schemas import processor_schema as ps
from ..schemas import chunk_schema as cs
from ..libs.id import IDLibs
from typing import List
import uuid


class ChunkHelper:

    @staticmethod
    async def inject(cp: ps.CommonParams, docs: List[Document]):
        chunks: List[cs.Chunk] = []
        for doc in docs:
            text = doc.page_content
            metadata = doc.metadata
            file_chunk_number = doc.metadata.pop("file_chunk_number")
            chunk_number = doc.metadata.pop("rag_chunk_number")
            chunk = cs.Chunk(
                chunk_id=IDLibs.generate_chunk_id(cp.doc_readable_id, chunk_number),
                chunk_number=chunk_number,
                text=text,
                file_chunk_number=file_chunk_number,
                metadata=metadata
            )
            chunks.append(chunk)
