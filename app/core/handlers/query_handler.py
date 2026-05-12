from ..services.query_service import QueryService
from ..schemas.query_schema import QueryType
from app.utils.logger import logger
from typing import Optional
import uuid


class QueryHandler:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.query_service = QueryService(org_id=org_id, project_id=project_id)

    async def query(self, query: str, query_type: QueryType, document_id: Optional[uuid.UUID] = None, top_k: int = 10):
        try:
            return await self.query_service.query(query=query, query_type=query_type, document_id=document_id, top_k=top_k)
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e
