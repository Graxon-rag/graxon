from ..schemas.document_processing_schema import (
    DocumentProcessingGetSchema,
    DocumentProcessingUpdateSchema,
    DocumentProcessingCreateSchema,
)
from ..databases.postgresql.models import DocumentProcessingState
from ..databases.postgresql.client import GPostgresqlClient
from datetime import datetime, timezone
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class DocumentProcessingRepo:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self.db = GPostgresqlClient()
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id

    async def create(self, c: DocumentProcessingCreateSchema) -> DocumentProcessingGetSchema:
        try:
            async with self.db.get_session() as session:
                record = DocumentProcessingState(
                    org_id=self.org_id,
                    project_id=self.project_id,
                    document_id=self.document_id,
                    **c.model_dump(exclude={"org_id", "project_id", "document_id"})
                )
                session.add(record)
                await session.commit()
                await session.refresh(record)

                return DocumentProcessingGetSchema.model_validate(record)
        except Exception as e:
            logger.error({
                "message": "Failed to create document processing state",
                "document_id": str(self.document_id),
                "error": str(e)
            })
            raise e

    async def update(self, u: DocumentProcessingUpdateSchema) -> DocumentProcessingGetSchema:
        try:
            async with self.db.get_session() as session:
                stmt = select(DocumentProcessingState).where(
                    DocumentProcessingState.org_id == self.org_id,
                    DocumentProcessingState.project_id == self.project_id,
                    DocumentProcessingState.document_id == self.document_id,
                )
                doc = await session.scalar(stmt)

                if doc is None:
                    raise ValueError(
                        f"Document processing state for document id {self.document_id} not found"
                    )

                update_data = u.model_dump(exclude_unset=True)

                for field, value in update_data.items():
                    setattr(doc, field, value)

                # Explicit updated_at touch if model doesn't auto-update
                if hasattr(doc, "updated_at"):
                    doc.updated_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(doc)

                return DocumentProcessingGetSchema.model_validate(doc)
        except Exception as e:
            logger.error({
                "message": "Failed to update document processing state",
                "document_id": str(self.document_id),
                "error": str(e)
            })
            raise e

    async def get_by_document(self) -> DocumentProcessingGetSchema | None:
        try:
            async with self.db.get_session() as session:
                stmt = select(DocumentProcessingState).where(
                    DocumentProcessingState.org_id == self.org_id,
                    DocumentProcessingState.project_id == self.project_id,
                    DocumentProcessingState.document_id == self.document_id,
                )
                doc = await session.scalar(stmt)

                if doc is None:
                    return None

                return DocumentProcessingGetSchema.model_validate(doc)
        except Exception as e:
            logger.error({
                "message": "Failed to get document processing state",
                "document_id": str(self.document_id),
                "error": str(e)
            })
            raise e
