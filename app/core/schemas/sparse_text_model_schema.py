from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import datetime
import uuid


class SparseModelProviderType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class SparseModelProvider(str, Enum):
    PINECONE = "pinecone"
    QDRANT = "qdrant"
    PRITHIVIDA = "prithivida"
    PRITHVIDA = "prithvida"


class SparseTextModelCreateSchema(BaseModel):

    org_id: str = Field(
        description="The organization id of the sparse text model",
    )
    name: str = Field(
        description="The name of the sparse text model",
    )
    provider_type: SparseModelProviderType = Field(
        description="The provider type of the sparse text model",
    )
    provider: SparseModelProvider = Field(
        description="The provider of the sparse text model",
    )
    model_name: str = Field(
        description="The model name of the sparse text model",
    )
    model_id: str = Field(
        description="The model id of the sparse text model",
    )
    description: str = Field(
        description="The description of the sparse text model",
    )
    model_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="The model metadata of the sparse text model",
    )
    size_in_gb: Optional[float] = Field(
        default=0.0,
        description="The size of the sparse text model in GB",
    )


class SparseTextModelGetSchema(BaseModel):

    id: uuid.UUID = Field(
        description="The id of the sparse text model",
    )
    org_id: str = Field(
        description="The organization id of the sparse text model",
    )
    name: str = Field(
        description="The name of the sparse text model",
    )
    provider_type: SparseModelProviderType = Field(
        description="The provider type of the sparse text model",
    )
    provider: SparseModelProvider = Field(
        description="The provider of the sparse text model",
    )
    model_name: str = Field(
        description="The model name of the sparse text model",
    )
    model_id: str = Field(
        description="The model id of the sparse text model",
    )
    description: str = Field(
        description="The description of the sparse text model",
    )
    model_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="The model metadata of the sparse text model",
    )
    size_in_gb: Optional[float] = Field(
        default=0.0,
        description="The size of the sparse text model in GB",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the sparse text model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the sparse text model",
    )
