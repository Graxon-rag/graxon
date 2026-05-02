from pydantic import BaseModel, Field
import uuid
import datetime


class ReRankerCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the reranker model",
    )
    name: str = Field(
        description="The name of the reranker model",
    )
    provider: str = Field(
        description="The provider of the reranker model",
    )
    model: str = Field(
        description="The model of the reranker model",
    )
    description: str = Field(
        description="The description of the reranker model",
    )
    size_in_gb: float = Field(
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
    provider: str = Field(
        description="The provider of the reranker model",
    )
    model: str = Field(
        description="The model of the reranker model",
    )
    description: str = Field(
        description="The description of the reranker model",
    )
    size_in_gb: float = Field(
        description="The size of the reranker model in GB",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the reranker model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the reranker model",
    )
