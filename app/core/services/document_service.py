from app.utils.logger import logger
from fastapi import UploadFile
from ..schemas.document_schema import DocumentUploadSchema, DocumentGetSignedUrlSchema, DocumentUploadResponseSchema, DocumentCreateSchema, DocumentGetSchema
from ..services.project_service import ProjectService
from ..repos.document_repo import DocumentRepo
from ..rabbitmq.producer import GMQDocumentProducer
from app.constants.document import DocumentStatus
from ..helpers.minio_helper import MinioHelper
from ..libs.id import IDLibs
import uuid


class DocumentService:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self._project_service = ProjectService(org_id=self.org_id)
        self.minio_helper = MinioHelper(org_id=self.org_id, project_id=project_id)
        self._repo = DocumentRepo(org_id=self.org_id, project_id=project_id)

    async def handle_document_upload(self, data: DocumentUploadSchema, file: UploadFile) -> DocumentUploadResponseSchema:
        try:
            result = await self._handle_document_upload(data, file)
            return result
        except Exception as e:
            logger.error({"message": "Failed to upload document", "error": str(e)})
            raise e

    async def get_all(self) -> list[DocumentGetSchema]:
        try:
            return await self._repo.get_all()
        except Exception as e:
            logger.error({"message": "Failed to get documents", "error": str(e)})
            raise e

    async def get(self, document_id: uuid.UUID) -> DocumentGetSchema | None:
        try:
            return await self._repo.get(document_id)
        except Exception as e:
            logger.error({"message": "Failed to get document", "error": str(e)})
            raise e

    async def delete(self, document_id: uuid.UUID) -> bool:
        try:
            return await self._repo.delete(document_id)
        except Exception as e:
            logger.error({"message": "Failed to delete document", "error": str(e)})
            raise e

    async def get_document_signed_url(self, document: DocumentGetSignedUrlSchema):
        try:
            return await self.minio_helper.get_signed_url(document)
        except Exception as e:
            logger.error({"message": "Failed to get document signed url", "error": str(e)})
            raise e

    async def submit_process_document(self, document_id: uuid.UUID) -> bool:
        try:
            document = await self._repo.change_document_status(document_id, DocumentStatus.QUEUED)
            try:
                await GMQDocumentProducer.publish_to_processing_exchange(document)
            except Exception as e:
                await self._repo.change_document_status(document_id, DocumentStatus.PENDING)
                raise e
            return True
        except Exception as e:
            logger.error({"message": "Failed to process document", "error": str(e)})
            raise e

    async def change_document_status(self, document_id: uuid.UUID, status: DocumentStatus):
        try:
            return await self._repo.change_document_status(document_id, status)
        except Exception as e:
            logger.error({"message": "Failed to change document status", "error": str(e)})
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

            doc_create_schema = DocumentCreateSchema(
                org_id=self.org_id,
                project_id=project_id,
                readable_id=document_name_id,
                name=document.name,
                type=document.type,
                bucket=self.org_id,
                key=key,
                status=DocumentStatus.PENDING
            )

            await self._repo.create(doc_create_schema)

            result = DocumentUploadResponseSchema(
                org_id=self.org_id,
                project_id=project_id,
                bucket=self.org_id,
                key=key,
                signed_url=signed_url
            )

            return result

        except Exception as e:
            logger.error({"message": "Failed to upload document", "error": str(e)})
            raise e
