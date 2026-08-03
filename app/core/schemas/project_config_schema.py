from pydantic import BaseModel, Field
from typing import Optional
import datetime
import uuid


class ProjectConfigBaseSchema(BaseModel):
    project_id: uuid.UUID = Field(
        description="The project id of the config",
    )

    graph_db_enable: bool = Field(
        description="The graph db enable of the config",
    )

    reranker_enable: bool = Field(
        description="The reranker enable of the config",
    )

    sparse_embedding_enable: bool = Field(
        description="The sparse embedding enable of the config",
    )

    llm_tag_extraction_enable: bool = Field(
        description="The llm tag extraction enable of the config",
    )

    llm_model_id: uuid.UUID = Field(
        description="The llm model id of the config",
    )

    llm_model_credential_id: uuid.UUID = Field(
        description="The llm model credential id of the config",
    )

    embedding_model_id: uuid.UUID = Field(
        description="The embedding model id of the config",
    )

    embedding_model_credential_id: uuid.UUID = Field(
        description="The embedding model credential id of the config",
    )

    ocr_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The ocr model id of the config",
    )

    ocr_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The ocr model credential id of the config",
    )

    sparse_text_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The sparse text model id of the config",
    )

    sparse_text_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The sparse text model credential id of the config",
    )

    reranker_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The reranker model id of the config",
    )

    reranker_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The reranker model credential id of the config",
    )

    audio_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The audio model id of the config",
    )

    audio_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The audio model credential id of the config",
    )

    video_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The video model id of the config",
    )

    video_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The video model credential id of the config",
    )


class ProjectConfigCreateSchema(ProjectConfigBaseSchema):
    pass


class ProjectConfigGetSchema(ProjectConfigBaseSchema):
    id: uuid.UUID = Field(
        description="The id of the config",
    )

    created_at: datetime.datetime = Field(
        description="The created at of the config",
    )

    updated_at: datetime.datetime = Field(
        description="The updated at of the config",
    )
