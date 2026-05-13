from ..services.query_service import QueryService
from ..schemas.query_schema import GQuery
from app.utils.logger import logger
import uuid


class QueryHandler:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.query_service = QueryService(org_id=org_id, project_id=project_id)

    async def query(self, query: GQuery):
        try:
            return await self.query_service.query(query)
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e
