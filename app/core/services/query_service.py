from ..workflow.lgraph.graph import Graph
from app.utils.logger import logger
from typing import Optional
import uuid


class QueryService:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.graph = Graph(org_id=self.org_id, project_id=self.project_id)

    async def query(self, query: str, document_id: Optional[uuid.UUID] = None, top_k: int = 10):
        try:
            return await self.graph.query_documents(query=query, document_id=document_id, top_k=top_k)
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e
