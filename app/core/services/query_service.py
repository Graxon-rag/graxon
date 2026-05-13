from ..workflow.document_workflow import DocumentWorkflow
from ..schemas.query_schema import GQuery
from app.utils.logger import logger
import uuid


class QueryService:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.workflow = DocumentWorkflow(org_id=self.org_id, project_id=self.project_id)

    async def query(self, query: GQuery):
        try:
            return await self.workflow.query(query)
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e
