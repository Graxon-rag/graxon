from ..schemas.document_schema import DocumentGetSchema
from ..services.document_service import DocumentService
from ..services.project_service import ProjectService
from app.utils.logger import logger
import uuid


class DocumentWorkflow:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id

    async def process(self, document: DocumentGetSchema):
        pass
