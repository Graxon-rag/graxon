from app.utils.logger import logger
from ..services.document_service import DocumentService
from ..schemas.document_schema import DocumentUploadSchema, DocumentGetSignedUrlSchema, DocumentUploadResponseSchema
from fastapi import UploadFile
import uuid


class DocumentHandler:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.service = DocumentService(org_id=self.org_id, project_id=project_id)

    async def handle_document_upload(self, data: DocumentUploadSchema, file: UploadFile) -> DocumentUploadResponseSchema:
        try:
            return await self.service.handle_document_upload(data, file)
        except Exception as e:
            logger.error({"message": "Failed to upload document", "error": str(e)})
            raise e

    async def get_document_signed_url(self, document: DocumentGetSignedUrlSchema):
        try:
            return await self.service.get_document_signed_url(document)
        except Exception as e:
            logger.error({"message": "Failed to get document signed url", "error": str(e)})
            raise e
