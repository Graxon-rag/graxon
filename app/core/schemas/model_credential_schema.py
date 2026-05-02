from pydantic import BaseModel, Field
from app.constants.model_provider import ModelProvider
import uuid
import datetime


class ModelCredentialGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the model credential",
    )
    org_id: str = Field(
        description="The organization id of the model credential",
    )
    name: str = Field(
        description="The name of the model credential",
    )
    description: str = Field(
        description="The description of the model credential",
    )
    provider: ModelProvider = Field(
        description="The provider of the model credential",
    )
    api_key: str = Field(
        description="The api key of the model credential",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the model credential",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the model credential",
    )


class ModelCredentialCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the model credential",
    )
    name: str = Field(
        description="The name of the model credential",
    )
    description: str = Field(
        description="The description of the model credential",
    )
    provider: ModelProvider = Field(
        description="The provider of the model credential",
    )
    api_key: str = Field(
        description="The api key of the model credential",
    )
