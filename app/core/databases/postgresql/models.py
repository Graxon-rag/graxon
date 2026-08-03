from sqlalchemy import String, Uuid, ForeignKey, Float, TIMESTAMP, Integer, CheckConstraint, JSON, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.constants.document import DocumentStatus
from app.constants.postgresql import PGTables
from typing import Dict, Any, Optional
import datetime
import uuid


status_constraint_string = f"status in ('{DocumentStatus.PENDING}', '{DocumentStatus.PROCESSING}', '{DocumentStatus.PROCESSED}', '{DocumentStatus.FAILED}', '{DocumentStatus.QUEUED}')"


class Base(DeclarativeBase):
    pass


class Organization(Base):
    __tablename__ = PGTables.ORGANIZATION_TABLE
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Project(Base):
    __tablename__ = PGTables.PROJECT_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    readable_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    project_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default={})

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "readable_id": self.readable_id,
            "name": self.name,
            "description": self.description,
            "project_metadata": self.project_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ProjectConfig(Base):
    __tablename__ = PGTables.PROJECT_CONFIG_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Enable flags
    graph_db_enable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reranker_enable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sparse_embedding_enable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    llm_tag_extraction_enable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # LLM Mandatory
    llm_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("llm_models.id", ondelete="RESTRICT"), nullable=False)
    llm_model_credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_credentials.id", ondelete="RESTRICT"), nullable=False)

    # Embedding Mandatory
    embedding_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("embedding_models.id", ondelete="RESTRICT"), nullable=False)
    embedding_model_credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_credentials.id", ondelete="RESTRICT"), nullable=False)

    # OCR Optional
    ocr_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ocr_models.id", ondelete="RESTRICT"), nullable=True)
    ocr_model_credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_credentials.id", ondelete="RESTRICT"), nullable=True)

    # Sparse Optional
    sparse_text_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sparse_text_models.id", ondelete="RESTRICT"), nullable=True)
    sparse_text_model_credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_credentials.id", ondelete="RESTRICT"), nullable=True)

    # Reranker Optional
    reranker_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reranker_models.id", ondelete="RESTRICT"), nullable=True)
    reranker_model_credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_credentials.id", ondelete="RESTRICT"), nullable=True)

    # Audio Optional
    audio_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audio_models.id", ondelete="RESTRICT"), nullable=True)
    audio_model_credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_credentials.id", ondelete="RESTRICT"), nullable=True)

    # Video Optional
    video_model_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("video_models.id", ondelete="RESTRICT"), nullable=True)
    video_model_credential_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_credentials.id", ondelete="RESTRICT"), nullable=True)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "graph_db_enable": self.graph_db_enable,
            "reranker_enable": self.reranker_enable,
            "sparse_embedding_enable": self.sparse_embedding_enable,
            "llm_tag_extraction_enable": self.llm_tag_extraction_enable,
            "llm_model_id": self.llm_model_id,
            "llm_model_credential_id": self.llm_model_credential_id,
            "embedding_model_id": self.embedding_model_id,
            "embedding_model_credential_id": self.embedding_model_credential_id,
            "ocr_model_id": self.ocr_model_id,
            "ocr_model_credential_id": self.ocr_model_credential_id,
            "sparse_text_model_id": self.sparse_text_model_id,
            "sparse_text_model_credential_id": self.sparse_text_model_credential_id,
            "reranker_model_id": self.reranker_model_id,
            "reranker_model_credential_id": self.reranker_model_credential_id,
            "audio_model_id": self.audio_model_id,
            "audio_model_credential_id": self.audio_model_credential_id,
            "video_model_id": self.video_model_id,
            "video_model_credential_id": self.video_model_credential_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Document(Base):
    __tablename__ = PGTables.DOCUMENT_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    readable_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(255), nullable=False)
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(255), CheckConstraint(status_constraint_string), nullable=False)
    size: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "project_id": self.project_id,
            "name": self.name,
            "readable_id": self.readable_id,
            "type": self.type,
            "bucket": self.bucket,
            "key": self.key,
            "status": self.status,
            "size": self.size or None,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ModelCredential(Base):
    __tablename__ = PGTables.MODEL_CREDENTIAL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key: Mapped[str] = mapped_column(String(500), nullable=False)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "description": self.description,
            "provider": self.provider,
            "api_key": self.api_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class LLMModel(Base):
    __tablename__ = PGTables.LLM_MODEL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class EmbeddingModel(Base):
    __tablename__ = PGTables.EMBEDDING_MODEL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "dimension": self.dimension,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class SparseTextModel(Base):
    __tablename__ = PGTables.SPARSE_TEXT_MODEL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    model_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    size_in_gb: Mapped[float] = mapped_column(Float, nullable=True)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "provider_type": self.provider_type,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "size_in_gb": self.size_in_gb,
            "description": self.description,
            "model_metadata": self.model_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ReRankerModel(Base):
    __tablename__ = PGTables.RERANKER_MODEL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    model_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    size_in_gb: Mapped[float] = mapped_column(Float, nullable=True)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "provider_type": self.provider_type,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "size_in_gb": self.size_in_gb,
            "description": self.description,
            "model_metadata": self.model_metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class OCRModel(Base):
    __tablename__ = PGTables.OCR_MODEL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "model_metadata": self.model_metadata,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class AudioModel(Base):
    __tablename__ = PGTables.AUDIO_MODEL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "model_metadata": self.model_metadata,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class VideoModel(Base):
    __tablename__ = PGTables.VIDEO_MODEL_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    model_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "name": self.name,
            "provider": self.provider,
            "model_name": self.model_name,
            "model_id": self.model_id,
            "model_metadata": self.model_metadata,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Webhook(Base):
    __tablename__ = PGTables.WEBHOOK_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamp
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
        )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "project_id": self.project_id,
            "name": self.name,
            "url": self.url,
            "token": self.token,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
