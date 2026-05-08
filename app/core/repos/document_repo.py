from ..schemas.document_schema import DocumentGetSchema, DocumentCreateSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import Document
from ..helpers.minio_helper import MinioHelper
from app.constants.minio import MinioConstant
from app.constants.document import DocumentStatus
from ..qdrant.delete import QDrantCleaner
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class DocumentRepo:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.db = GPostgresqlClient()
        self.org_id = org_id
        self.project_id = project_id
        self.minio_helper = MinioHelper(org_id=self.org_id, project_id=self.project_id)
        self.qdrant_cleaner = QDrantCleaner(org_id=self.org_id, project_id=self.project_id)

    async def create(self, doc: DocumentCreateSchema) -> DocumentGetSchema:
        try:
            async with self.db.get_session() as session:
                new_doc = Document(
                    org_id=self.org_id,
                    project_id=self.project_id,
                    readable_id=doc.readable_id,
                    name=doc.name,
                    type=doc.type,
                    bucket=doc.bucket,
                    key=doc.key,
                    status=doc.status
                )
                session.add(new_doc)
                await session.commit()

                return DocumentGetSchema(**new_doc.to_dict())

        except Exception as e:
            logger.error({"message": "Failed to create document", "error": str(e)})
            raise e

    async def create_multiple(self, docs: list[DocumentCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                doc_models = [Document(**doc.model_dump()) for doc in docs]
                session.add_all(doc_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create document", "error": str(e)})
            raise e

    async def get_all(self) -> list[DocumentGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(Document)
                stmt = stmt.where(Document.org_id == self.org_id)
                stmt = stmt.where(Document.project_id == self.project_id)
                stmt = stmt.order_by(Document.created_at.desc())
                pg_result = await session.execute(stmt)
                result_list = list(pg_result.scalars().all())
                return [DocumentGetSchema(**doc.to_dict()) for doc in result_list]
        except Exception as e:
            logger.error({"message": "Failed to get documents", "error": str(e)})
            raise e

    async def get(self, document_id: uuid.UUID) -> DocumentGetSchema | None:
        try:
            async with self.db.get_session() as session:
                stmt = select(Document)
                stmt = stmt.where(Document.id == document_id)
                stmt = stmt.where(Document.org_id == self.org_id)
                stmt = stmt.where(Document.project_id == self.project_id)

                document = await session.scalar(stmt)
                if document is None:
                    raise Exception(f"Document with id {document_id} not found")
                return DocumentGetSchema(**document.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get document", "error": str(e)})
            raise e

    async def delete(self, document_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                document = await session.scalar(select(Document).where(Document.id == document_id))
                if document is None:
                    raise Exception(f"Document with id {document_id} not found")

                key = document.key
                bucket = document.bucket
                await self.minio_helper.delete_file(bucket=bucket, key=key)

                await session.delete(document)
                await session.commit()

                try:
                    lexical_engine_output_file = MinioConstant.LEXICAL_ENGINE_OUTPUT_FILE
                    leo_key = f"{self.project_id}/{document.readable_id}/{lexical_engine_output_file}.json"
                    seo_key = f"{self.project_id}/{document.readable_id}/{MinioConstant.SPARSE_EMBEDDING_OUTPUT_FILE}.json"
                    eo_key = f"{self.project_id}/{document.readable_id}/{MinioConstant.EMBEDDING_OUTPUT_FILE}.json"
                    await self.minio_helper.delete_file(bucket=bucket, key=seo_key)
                    await self.minio_helper.delete_file(bucket=bucket, key=eo_key)
                    await self.minio_helper.delete_file(bucket=bucket, key=leo_key)

                except Exception as e:
                    logger.warning({"message": "Failed to delete lexical engine output, sparse embedding output or embedding output file", "error": str(e)})

                return True
        except Exception as e:
            logger.error({"message": "Failed to delete document", "error": str(e)})
            raise e

    async def change_document_status(self, document_id: uuid.UUID, status: DocumentStatus) -> DocumentGetSchema:
        try:
            async with self.db.get_session() as session:
                document = await session.scalar(select(Document).where(Document.id == document_id))
                if document is None:
                    raise Exception(f"Document with id {document_id} not found")

                logger.info({"message": "Changing document status", "document_id": document_id, "status": status})

                document.status = status
                await session.commit()
                return DocumentGetSchema(**document.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to change document status", "error": str(e)})
            raise e
