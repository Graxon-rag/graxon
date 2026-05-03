from app.utils.logger import logger
from fastapi import UploadFile
from ..schemas.document_schema import DocumentUploadSchema, DocumentGetSignedUrlSchema, DocumentUploadResponseSchema
from ..services.project_service import ProjectService
from ..databases.minio.client import GMinioClient
from app.config.env import Env
from ..helpers.minio_helper import MinioHelper
from types_aiobotocore_s3 import S3Client
from ..libs.id import IDLibs
from typing import cast
import uuid


class DocumentService:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self._project_service = ProjectService(org_id=self.org_id)
        self.minio_helper = MinioHelper(org_id=self.org_id, project_id=project_id)

    async def handle_document_upload(self, data: DocumentUploadSchema, file: UploadFile) -> DocumentUploadResponseSchema:
        try:
            return await self._handle_document_upload(data, file)
        except Exception as e:
            logger.error({"message": "Failed to upload document", "error": str(e)})
            raise e

    async def get_document_signed_url(self, document: DocumentGetSignedUrlSchema):
        try:
            return await self.minio_helper.get_signed_url(document)
        except Exception as e:
            logger.error({"message": "Failed to get document signed url", "error": str(e)})
            raise e

    async def _handle_document_upload(self, document: DocumentUploadSchema, file: UploadFile) -> DocumentUploadResponseSchema:
        try:
            project_id = document.project_id

            project = await self._project_service.get(project_id)
            if not project:
                raise Exception(f"Project with id {project_id} not found")

            project_name = project.readable_id

            document_name_id = IDLibs.generate_document_id(project_name)

            (key, signed_url) = await self.minio_helper.upload_file(file, document.type, document.name, document_name_id)

            return DocumentUploadResponseSchema(
                org_id=self.org_id,
                project_id=project_id,
                bucket=self.org_id,
                key=key,
                signed_url=signed_url
            )

        except Exception as e:
            logger.error({"message": "Failed to upload document", "error": str(e)})
            raise e
