from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum
import datetime
import uuid


class RerankerModelProviderType(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"


class RerankerModelProvider(str, Enum):
    XENOVA = "xenova"
    BBAI = "baai"
    JINA = "jina"
    COHERE = "cohere"
    VOYAGE = "voyage"


class ReRankerCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the reranker model",
    )
    name: str = Field(
        description="The name of the reranker model",
    )
    provider_type: RerankerModelProviderType = Field(
        description="The provider type of the reranker model",
    )
    provider: RerankerModelProvider = Field(
        description="The provider of the reranker model",
    )
    model_name: str = Field(
        description="The model name of the reranker model",
    )
    model_id: str = Field(
        description="The model id of the reranker model",
    )
    description: str = Field(
        description="The description of the reranker model",
    )
    model_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="The model metadata of the reranker model",
    )
    size_in_gb: Optional[float] = Field(
        default=0.0,
        description="The size of the reranker model in GB",
    )


class ReRankerGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the reranker model",
    )
    org_id: str = Field(
        description="The organization id of the reranker model",
    )
    name: str = Field(
        description="The name of the reranker model",
    )
    provider_type: RerankerModelProviderType = Field(
        description="The provider type of the reranker model",
    )
    provider: RerankerModelProvider = Field(
        description="The provider of the reranker model",
    )
    model_name: str = Field(
        description="The model name of the reranker model",
    )
    model_id: str = Field(
        description="The model id of the reranker model",
    )
    description: str = Field(
        description="The description of the reranker model",
    )
    model_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="The model metadata of the reranker model",
    )
    size_in_gb: Optional[float] = Field(
        default=0.0,
        description="The size of the reranker model in GB",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the reranker model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the reranker model",
    )
