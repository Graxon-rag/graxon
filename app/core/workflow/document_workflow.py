from ..schemas import processor_schema as ps
from ..schemas.query_schema import GQuery
from ..schemas import chunk_schema as cs
from app.utils.logger import logger
from .lgraph.graph import Graph
from typing import List
import uuid


class DocumentWorkflow:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.graph = Graph(org_id=self.org_id, project_id=self.project_id)

    async def process(self, cp: ps.CommonParams, chunks: List[cs.Chunk]):
        try:
            pass
            # return result
        except Exception as e:
            logger.error({"message": "Failed to process document", "error": str(e)})
            raise e

    async def query(self, query: GQuery):
        try:
            pass
            # providers = await self._get_query_providers()
            # return await self.graph.query_documents(providers, query)
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e
