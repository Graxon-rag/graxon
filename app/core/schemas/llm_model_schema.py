from pydantic import BaseModel, Field
from app.constants.model_provider import LLMModelProvider
import datetime
import uuid


class LLMModelCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the LLM model",
    )
    name: str = Field(
        description="The name of the LLM model",
    )
    provider: LLMModelProvider = Field(
        description="The provider of the LLM model",
    )
    model_name: str = Field(
        description="The model name of the LLM model",
    )
    model_id: str = Field(
        description="The model id of the LLM model",
    )
    description: str = Field(
        description="The description of the LLM model",
    )


class LLMModelGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the LLM model",
    )
    org_id: str = Field(
        description="The organization id of the LLM model",
    )
    name: str = Field(
        description="The name of the LLM model",
    )
    provider: LLMModelProvider = Field(
        description="The provider of the LLM model",
    )
    model_name: str = Field(
        description="The model name of the LLM model",
    )
    model_id: str = Field(
        description="The model id of the LLM model",
    )
    description: str = Field(
        description="The description of the LLM model",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the LLM model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the LLM model",
    )
