from ..schemas.document_schema import DocumentGetSchema, DocumentCreateSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import Document
from app.constants.document import DocumentStatus
from ..helpers.minio_helper import MinioHelper
from app.constants.minio import MinioConstant
from ..neo4j.document import GN4jDocument
from ..qdrant.delete import QDrantCleaner
from ..neo4j.chunk import GN4jChunk
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
        self.neo4j_document = GN4jDocument(org_id=self.org_id, project_id=self.project_id)
        self.neo4j_chunk = GN4jChunk(org_id=self.org_id, project_id=self.project_id)

    async def create(self, doc: DocumentCreateSchema) -> DocumentGetSchema:
        try:
            async with self.db.get_session() as session:
                new_doc = Document(
                    id=doc.id,
                    org_id=self.org_id,
                    project_id=self.project_id,
                    readable_id=doc.readable_id,
                    name=doc.name,
                    type=doc.type,
                    bucket=doc.bucket,
                    key=doc.key,
                    status=doc.status,
                    size=doc.size
                )
                session.add(new_doc)
                await self.neo4j_document.create(new_doc.id, new_doc.readable_id)
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

                await self.neo4j_chunk.delete_by_doc_id(document_id)
                await self.neo4j_document.delete(document_id)
                await session.delete(document)
                await session.commit()

                try:
                    files_to_delete = [
                        MinioConstant.SPARSE_EMBEDDING_OUTPUT_FILE,
                        MinioConstant.EMBEDDING_OUTPUT_FILE,
                        MinioConstant.LEXICAL_ENGINE_OUTPUT_FILE,
                        MinioConstant.LLM_OUTPUT_FILE,
                        MinioConstant.LLM_TAG_RESPONSE,
                        MinioConstant.N4J_EDGES_NEXT_PREV_OUTPUT,
                        MinioConstant.N4J_EDGES_TAG_OUTPUT,
                        MinioConstant.N4J_EDGES_REFERENCE_OUTPUT,
                        MinioConstant.CHUNKS_OUTPUT_FILE,
                    ]

                    for file_name in files_to_delete:
                        key = f"{self.project_id}/{document.readable_id}/{file_name}.json"

                        try:
                            await self.minio_helper.delete_file(
                                bucket=bucket,
                                key=key
                            )

                            logger.info({
                                "message": "Deleted file from MinIO",
                                "key": key
                            })

                        except Exception as delete_error:
                            logger.warning({
                                "message": "Failed to delete file from MinIO",
                                "key": key,
                                "error": str(delete_error)
                            })

                except Exception as e:
                    logger.warning({
                        "message": "Unexpected error during MinIO cleanup",
                        "error": str(e)
                    })

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
