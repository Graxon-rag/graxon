from .sparse_text_model_schema import SparseTextModelGetSchema
from .model_credential_schema import ModelCredentialGetSchema
from .embedding_model_schema import EmbeddingModelGetSchema
from .video_model_schema import VideoModelGetSchema
from .audio_model_schema import AudioModelGetSchema
from .ocr_model_schema import OCRModelGetSchema
from .llm_model_schema import LLMModelGetSchema
from .reranker_schema import ReRankerGetSchema
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

    reranker_enable: bool = Field(
        description="Whether reranker is enabled",
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
    reranker_enable: Optional[bool] = Field(
        default=None,
        description="Whether reranker is enabled",
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


class ProjectConfigDetailGetSchema(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID

    graph_db_enable: bool
    sparse_embedding_enable: bool
    llm_tag_extraction_enable: bool
    reranker_enable: bool

    llm_model: Optional[LLMModelGetSchema] = None
    embedding_model: Optional[EmbeddingModelGetSchema] = None
    reranker_model: Optional[ReRankerGetSchema] = None
    sparse_text_model: Optional[SparseTextModelGetSchema] = None
    reranker_model: Optional[ReRankerGetSchema] = None
    ocr_model: Optional[OCRModelGetSchema] = None
    audio_model: Optional[AudioModelGetSchema] = None
    video_model: Optional[VideoModelGetSchema] = None

    llm_model_credential: Optional[ModelCredentialGetSchema] = None
    embedding_model_credential: Optional[ModelCredentialGetSchema] = None
    sparse_text_model_credential: Optional[ModelCredentialGetSchema] = None
    reranker_model_credential: Optional[ModelCredentialGetSchema] = None
    ocr_model_credential: Optional[ModelCredentialGetSchema] = None
    audio_model_credential: Optional[ModelCredentialGetSchema] = None
    video_model_credential: Optional[ModelCredentialGetSchema] = None

    created_at: datetime.datetime = Field(
            description="The created at of the config",
        )

    updated_at: datetime.datetime = Field(
        description="The updated at of the config",
    )
