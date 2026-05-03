from pydantic import BaseModel, Field
import uuid
import datetime


class ProjectGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the project",
    )
    readable_id: str = Field(
        description="The readable id of the project",
    )
    org_id: str = Field(
        description="The organization id of the project",
    )
    name: str = Field(
        description="The name of the project",
    )
    description: str = Field(
        description="The description of the project",
    )
    llm_model_id: uuid.UUID = Field(
        description="The LLM model id of the project",
    )
    embedding_model_id: uuid.UUID = Field(
        description="The embedding model id of the project",
    )
    sparse_text_model_id: uuid.UUID = Field(
        description="The sparse text model id of the project",
    )
    reranker_model_id: uuid.UUID = Field(
        description="The reranker model id of the project",
    )
    llm_model_credential_id: uuid.UUID = Field(
        description="The LLM model credential id of the project",
    )
    embedding_model_credential_id: uuid.UUID = Field(
        description="The embedding model credential id of the project",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the project",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the project",
    )


class ProjectCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the project",
    )
    name: str = Field(
        description="The name of the project",
    )
    description: str = Field(
        description="The description of the project",
    )
    llm_model_id: uuid.UUID = Field(
        description="The LLM model id of the project",
    )
    embedding_model_id: uuid.UUID = Field(
        description="The embedding model id of the project",
    )
    sparse_text_model_id: uuid.UUID = Field(
        description="The sparse text model id of the project",
    )
    reranker_model_id: uuid.UUID = Field(
        description="The reranker model id of the project",
    )
    llm_model_credential_id: uuid.UUID = Field(
        description="The LLM model credential id of the project",
    )
    embedding_model_credential_id: uuid.UUID = Field(
        description="The embedding model credential id of the project",
    )
