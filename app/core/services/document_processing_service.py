from ..schemas.document_processing_schema import (
    DocumentProcessingGetSchema,
    DocumentProcessingUpdateSchema,
    DocumentProcessingCreateSchema,
)
from ..repos.document_processing_repo import DocumentProcessingRepo
from app.utils.logger import logger
import uuid


class DocumentProcessingService:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self.repo = DocumentProcessingRepo(org_id, project_id, document_id)
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id

    async def create(self, c: DocumentProcessingCreateSchema) -> DocumentProcessingGetSchema:
        try:
            return await self.repo.create(c)
        except Exception as e:
            logger.error({
                "message": "Failed to create document processing state",
                "document_id": str(self.document_id),
                "error": str(e)
            })
            raise e

    async def update(self, u: DocumentProcessingUpdateSchema) -> DocumentProcessingGetSchema:
        try:
            return await self.repo.update(u)
        except Exception as e:
            logger.error({
                "message": "Failed to update document processing state",
                "document_id": str(self.document_id),
                "error": str(e)
            })
            raise e

    async def get_by_document(self) -> DocumentProcessingGetSchema | None:
        try:
            return await self.repo.get_by_document()
        except Exception as e:
            logger.error({
                "message": "Failed to get document processing state",
                "document_id": str(self.document_id),
                "error": str(e)
            })
            raise e
