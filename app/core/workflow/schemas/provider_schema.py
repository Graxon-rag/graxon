from pydantic import BaseModel, Field
from app.constants.model_provider import ModelProvider, EmbeddingModelProvider, LLMModelProvider
from typing import Optional
import uuid


class LLMProviderSchema(BaseModel):
    provider: LLMModelProvider
    api_key: str
    model: str


class EmbeddingProviderSchema(BaseModel):
    provider: EmbeddingModelProvider
    api_key: str
    model: str


class SparseModelProviderSchema(BaseModel):
    provider: Optional[str] = None
    model: str = "Qdrant/bm42-all-minilm-l6-v2-attentions"


class RerankerProviderSchema(BaseModel):
    provider: Optional[str] = None
    model: str = "jinaai/jina-reranker-v1-turbo-en"


class ProviderSchema(BaseModel):
    org_id: str
    project_id: uuid.UUID
    document_id: uuid.UUID
    llm: LLMProviderSchema
    embedding: EmbeddingProviderSchema
    sparse_model: SparseModelProviderSchema
    reranker: RerankerProviderSchema
