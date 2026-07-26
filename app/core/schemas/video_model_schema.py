from app.constants.model_provider import VideoModelProvider
from pydantic import BaseModel, Field
import datetime
import uuid


class VideoModelGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the video model",
    )
    org_id: str = Field(
        description="The organization id of the video model",
    )
    name: str = Field(
        description="The name of the video model",
    )
    provider: VideoModelProvider = Field(
        description="The provider of the video model",
    )
    model_name: str = Field(
        description="The model name of the video model",
    )
    model_id: str = Field(
        description="The model id of the video model",
    )
    description: str = Field(
        description="The description of the video model",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the video model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the video model",
    )


class VideoModelCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the video model",
    )
    name: str = Field(
        description="The name of the video model",
    )
    provider: VideoModelProvider = Field(
        description="The provider of the video model",
    )
    model_name: str = Field(
        description="The model name of the video model",
    )
    model_id: str = Field(
        description="The model id of the video model",
    )
    description: str = Field(
        description="The description of the video model",
    )
