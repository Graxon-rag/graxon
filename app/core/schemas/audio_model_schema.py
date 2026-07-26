from app.constants.model_provider import AudioModelProvider
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime
import uuid


class AudioModelGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the audio model",
    )
    org_id: str = Field(
        description="The organization id of the audio model",
    )
    name: str = Field(
        description="The name of the audio model",
    )
    provider: AudioModelProvider = Field(
        description="The provider of the audio model",
    )
    model_name: str = Field(
        description="The model name of the audio model",
    )
    model_id: str = Field(
        description="The model id of the audio model",
    )
    model_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="The model metadata of the audio model",
    )
    description: str = Field(
        description="The description of the audio model",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the audio model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the audio model",
    )


class AudioModelCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the audio model",
    )
    name: str = Field(
        description="The name of the audio model",
    )
    provider: AudioModelProvider = Field(
        description="The provider of the audio model",
    )
    model_name: str = Field(
        description="The model name of the audio model",
    )
    model_id: str = Field(
        description="The model id of the audio model",
    )
    description: str = Field(
        description="The description of the audio model",
    )
    model_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="The model metadata of the audio model",
    )
