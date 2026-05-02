from pydantic import BaseModel, Field
import uuid
import datetime


class SparseTextModelCreateSchema(BaseModel):
    
    org_id: str = Field(
        description="The organization id of the sparse text model",
    )
    name: str = Field(
        description="The name of the sparse text model",
    )
    provider: str = Field(
        description="The provider of the sparse text model",
    )
    model: str = Field(
        description="The model of the sparse text model",
    )
    description: str = Field(
        description="The description of the sparse text model",
    )
    size_in_gb: float = Field(
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
    provider: str = Field(
        description="The provider of the sparse text model",
    )
    model: str = Field(
        description="The model of the sparse text model",
    )
    description: str = Field(
        description="The description of the sparse text model",
    )
    size_in_gb: float = Field(
        description="The size of the sparse text model in GB",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the sparse text model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the sparse text model",
    )
