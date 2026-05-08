from pydantic import BaseModel
from typing import Optional
from fastembed.sparse.sparse_embedding_base import SparseEmbedding


class Chunk(BaseModel):
    chunk_id: str
    chunk_number: int
    text: str
    title: Optional[str] = None
    source: Optional[str] = None
    page_number: Optional[int] = None    


class ChunkEmbedding(BaseModel):
    chunk_id: str
    chunk_number: int
    embedding: list[float]


class ChunkSparseEmbedding(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    chunk_id: str
    chunk_number: int
    embedding: SparseEmbedding
