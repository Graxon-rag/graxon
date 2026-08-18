from .project_variables_schema import ProjectVariableCreateSchema
from .sparse_text_model_schema import SparseTextModelGetSchema
from .model_credential_schema import ModelCredentialGetSchema
from .project_config_schema import ProjectConfigCreateSchema
from .embedding_model_schema import EmbeddingModelGetSchema
from .llm_model_schema import LLMModelGetSchema
from .reranker_schema import ReRankerGetSchema
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime
import uuid


class ProjectCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the project",
    )
    name: str = Field(
        description="The name of the project",
    )
    config: ProjectConfigCreateSchema
    variables: ProjectVariableCreateSchema
    description: str = Field(
        description="The description of the project",
    )
    project_metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="The project metadata of the project",
    )


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
    created_at: datetime.datetime = Field(
        description="The created at of the project",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the project",
    )


class ProjectDetailMetadata(BaseModel):
    llm_model: Optional[LLMModelGetSchema] = None
    embedding_model: Optional[EmbeddingModelGetSchema] = None 
    sparse_text_model: Optional[SparseTextModelGetSchema] = None
    reranker: Optional[ReRankerGetSchema] = None
    llm_model_credential: Optional[ModelCredentialGetSchema] = None
    embedding_model_credential: Optional[ModelCredentialGetSchema] = None


class ProjectDetailSchema(BaseModel):

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

    details: ProjectDetailMetadata
