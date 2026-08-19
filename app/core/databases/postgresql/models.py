from sqlalchemy import String, Uuid, ForeignKey, Float, TIMESTAMP, Integer, CheckConstraint, JSON, Boolean, Text, func
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
    project_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True, default={})

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


class ProjectVariable(Base):
    __tablename__ = PGTables.PROJECT_VARIABLES_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey(f"{PGTables.PROJECT_TABLE}.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # External Call / Batching
    embedding_chunk_batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    sparse_chunk_batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    llm_tag_extraction_batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    delay_between_chunk_processing_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    # Chunks & Processing Limits
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=1500)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=200)
    max_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=10000)
    max_chunk_size_mb: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    max_pages_per_batch: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    tail_carry_chars: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    group_size_for_rag_chunk: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_group_size_for_rag_chunk: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    objects_per_buffer: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    rows_per_io_buffer: Mapped[int] = mapped_column(Integer, nullable=False, default=500)

    # Video Processing
    video_segment_duration_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    video_overlap_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    video_max_duration_per_rag_chunk: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    video_max_words_per_rag_chunk: Mapped[int] = mapped_column(Integer, nullable=False, default=300)

    # Audio Processing
    audio_segment_duration_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    audio_overlap_minutes: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    audio_max_duration_per_rag_chunk: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    audio_max_words_per_rag_chunk: Mapped[int] = mapped_column(Integer, nullable=False, default=300)

    # Vector Similarity Thresholds
    gte_edge_vector_similar_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.75)
    gte_edge_vector_similar_top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    gte_qdrant_point_score_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.45)

    # Expert Query
    eq_max_lane_count: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    eq_max_lane_entity: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    eq_gte_lane_weight_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    eq_max_lane_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    eq_max_chunks: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Timestamps
    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "embedding_chunk_batch_size": self.embedding_chunk_batch_size,
            "sparse_chunk_batch_size": self.sparse_chunk_batch_size,
            "llm_tag_extraction_batch_size": self.llm_tag_extraction_batch_size,
            "delay_between_chunk_processing_seconds": self.delay_between_chunk_processing_seconds,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "max_chunks": self.max_chunks,
            "max_chunk_size_mb": self.max_chunk_size_mb,
            "max_pages_per_batch": self.max_pages_per_batch,
            "tail_carry_chars": self.tail_carry_chars,
            "group_size_for_rag_chunk": self.group_size_for_rag_chunk,
            "max_group_size_for_rag_chunk": self.max_group_size_for_rag_chunk,
            "objects_per_buffer": self.objects_per_buffer,
            "rows_per_io_buffer": self.rows_per_io_buffer,
            "video_segment_duration_minutes": self.video_segment_duration_minutes,
            "video_overlap_minutes": self.video_overlap_minutes,
            "video_max_duration_per_rag_chunk": self.video_max_duration_per_rag_chunk,
            "video_max_words_per_rag_chunk": self.video_max_words_per_rag_chunk,
            "audio_segment_duration_minutes": self.audio_segment_duration_minutes,
            "audio_overlap_minutes": self.audio_overlap_minutes,
            "audio_max_duration_per_rag_chunk": self.audio_max_duration_per_rag_chunk,
            "audio_max_words_per_rag_chunk": self.audio_max_words_per_rag_chunk,
            "gte_edge_vector_similar_threshold": self.gte_edge_vector_similar_threshold,
            "gte_edge_vector_similar_top_k": self.gte_edge_vector_similar_top_k,
            "gte_qdrant_point_score_threshold": self.gte_qdrant_point_score_threshold,
            "eq_max_lane_count": self.eq_max_lane_count,
            "eq_max_lane_entity": self.eq_max_lane_entity,
            "eq_gte_lane_weight_threshold": self.eq_gte_lane_weight_threshold,
            "eq_max_lane_chunks": self.eq_max_lane_chunks,
            "eq_max_chunks": self.eq_max_chunks,
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
    is_ocr_needed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
            "is_ocr_needed": self.is_ocr_needed,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class DocumentProcessingState(Base):
    __tablename__ = PGTables.DOCUMENT_PROCESSING_STATE_TABLE

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(
        ForeignKey(f"{PGTables.ORGANIZATION_TABLE}.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{PGTables.PROJECT_TABLE}.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{PGTables.DOCUMENT_TABLE}.id", ondelete="CASCADE"), 
        nullable=False, 
        unique=True,  # Guarantees exactly 1 state row per document
        index=True
    )

    status: Mapped[str] = mapped_column(String(255), nullable=False)
    last_file_chunk_number: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=-1, 
        server_default="-1"
    )
    next_rag_start_index: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0, 
        server_default="0"
    )
    next_start_row: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_start_object: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_start_unit: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    next_start_page: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        server_default=func.now()
    )

    def to_dict(self):
        return {
            "id": self.id,
            "org_id": self.org_id,
            "project_id": self.project_id,
            "document_id": self.document_id,
            "status": self.status,
            "last_file_chunk_number": self.last_file_chunk_number,
            "next_rag_start_index": self.next_rag_start_index,
            "next_start_row": self.next_start_row,
            "next_start_object": self.next_start_object,
            "next_start_unit": self.next_start_unit,
            "next_start_page": self.next_start_page,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class Chunk(Base):
    __tablename__ = PGTables.CHUNK_TABLE
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{PGTables.DOCUMENT_TABLE}.id", ondelete="CASCADE"), nullable=False, index=True)

    chunk_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    chunk_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    file_chunk_number: Mapped[int] = mapped_column(Integer, nullable=True)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True, default={})

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
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "chunk_number": self.chunk_number,
            "text": self.text,
            "file_chunk_number": self.file_chunk_number,
            "metadata": self.chunk_metadata,
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
