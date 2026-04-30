import uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Uuid, JSON, Float, TIMESTAMP, Integer
import datetime


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    llm_model_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    embedding_model_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    sparse_text_model_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    reranker_model_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    
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


class LLMModel(Base):
    __tablename__ = "llm_models"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    
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
            "model": self.model,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    
class EmbeddingModel(Base):
    __tablename__ = "embedding_models"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
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
            "model": self.model,
            "dimension": self.dimension,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class SparseTextModel(Base):
    __tablename__ = "sparse_text_models"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    size_in_gb: Mapped[float] = mapped_column(Float, nullable=False)

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
            "model": self.model,
            "size_in_gb": self.size_in_gb,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

class ReRankerModel(Base):
    __tablename__ = "reranker_models"
    
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    size_in_gb: Mapped[float] = mapped_column(Float, nullable=False)
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
            "model": self.model,
            "size_in_gb": self.size_in_gb,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
