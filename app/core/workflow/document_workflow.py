from ..schemas import processor_schema as ps
from ..schemas.query_schema import GQuery
from ..schemas import chunk_schema as cs
from typing import List, AsyncGenerator
from app.utils.logger import logger
from .lgraph.graph import Graph
import uuid


class DocumentWorkflow:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.graph = Graph(org_id=self.org_id, project_id=self.project_id)

    async def process(self, cp: ps.CommonParams, chunks: List[cs.Chunk]):
        try:
            result = await self.graph.inject_document(cp, chunks)
            return result
        except Exception as e:
            logger.error({"message": "Failed to process document", "error": str(e)})
            raise e

    async def query(self, query: GQuery):
        """Handles standard, non-streaming queries."""
        try:
            return await self.graph.query_documents(query)
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e

    def stream_query(self, query: GQuery) -> AsyncGenerator[str, None]:
        """Handles streaming queries. Returns an AsyncGenerator for Server-Sent Events."""
        try:
            return self.graph.stream_query_documents(query)
        except Exception as e:
            logger.error({"message": "Failed to stream query", "error": str(e)})
            raise e
