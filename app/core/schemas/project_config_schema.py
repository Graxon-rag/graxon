from pydantic import BaseModel, Field
from typing import Optional
import datetime
import uuid


class ProjectConfigModelsSchema(BaseModel):
    llm_model_id: uuid.UUID = Field(
        description="The LLM model id",
    )

    llm_model_credential_id: uuid.UUID = Field(
        description="The LLM model credential id",
    )

    sparse_text_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The sparse text model id",
    )

    sparse_text_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The sparse text model credential id",
    )

    reranker_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The reranker model id",
    )

    reranker_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The reranker model credential id",
    )

    ocr_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The OCR model id",
    )

    ocr_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The OCR model credential id",
    )

    audio_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The audio model id",
    )

    audio_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The audio model credential id",
    )

    video_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The video model id",
    )

    video_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The video model credential id",
    )


class ProjectConfigCreateSchema(ProjectConfigModelsSchema):

    graph_db_enable: bool = Field(
        description="Whether graph database is enabled",
    )

    sparse_embedding_enable: bool = Field(
        description="Whether sparse embedding is enabled",
    )

    embedding_model_id: uuid.UUID = Field(
        description="The embedding model id",
    )

    embedding_model_credential_id: uuid.UUID = Field(
        description="The embedding model credential id",
    )

    llm_tag_extraction_enable: bool = Field(
        description="Whether LLM tag extraction is enabled",
    )


class ProjectConfigUpdateSchema(BaseModel):
    llm_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The LLM model id",
    )

    llm_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The LLM model credential id",
    )

    sparse_text_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The sparse text model id",
    )

    sparse_text_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The sparse text model credential id",
    )

    reranker_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The reranker model id",
    )

    reranker_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The reranker model credential id",
    )

    ocr_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The OCR model id",
    )

    ocr_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The OCR model credential id",
    )

    audio_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The audio model id",
    )

    audio_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The audio model credential id",
    )

    video_model_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The video model id",
    )

    video_model_credential_id: Optional[uuid.UUID] = Field(
        default=None,
        description="The video model credential id",
    )

    llm_tag_extraction_enable: Optional[bool] = Field(
        default=None,
        description="Whether LLM tag extraction is enabled",
    )


class ProjectConfigGetSchema(
    ProjectConfigCreateSchema
):
    id: uuid.UUID = Field(
        description="The id of the config",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the config",
    )

    created_at: datetime.datetime = Field(
        description="The created at of the config",
    )

    updated_at: datetime.datetime = Field(
        description="The updated at of the config",
    )
