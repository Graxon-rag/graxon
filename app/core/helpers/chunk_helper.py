from langchain_core.documents import Document
from ..schemas import processor_schema as ps
from typing import List
import uuid


class ChunkHelper:

    @staticmethod
    async def inject(cp: ps.CommonParams, chunks: List[Document]):
        pass
