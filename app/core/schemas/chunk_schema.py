from pydantic import BaseModel, model_serializer
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

    @model_serializer
    def serialize(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "chunk_number": self.chunk_number,
            "embedding": {
                "indices": self.embedding.indices.tolist(),
                "values": self.embedding.values.tolist(),
            }
        }
