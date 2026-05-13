from pydantic import BaseModel, model_serializer, Field, field_validator, model_validator
from typing import Optional, List
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


class SimilarTag(BaseModel):
    tag: str
    confidence: float  # 0.0 - 1.0

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, v: str) -> str:
        return v.strip().lower().replace(" ", "_")

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return round(max(0.0, min(1.0, v)), 2)


class TagResponse(BaseModel):
    new_tags: List[str]
    similar_tags: List[SimilarTag]
    has_backward_reference: bool
    reference_hint: Optional[str]

    @field_validator("new_tags")
    @classmethod
    def normalize_new_tags(cls, v: List[str]) -> List[str]:
        cleaned = [tag.strip().lower().replace(" ", "_") for tag in v]
        return cleaned[:2]

    @model_validator(mode="after")
    def validate_reference_hint(self) -> "TagResponse":
        if self.has_backward_reference and not self.reference_hint:
            self.reference_hint = "previous"
        if not self.has_backward_reference:
            self.reference_hint = None
        return self

    def validate_similar_tags_against_pool(self, global_tags: List[str]) -> "TagResponse":
        self.similar_tags = [st for st in self.similar_tags if st.tag in global_tags]
        return self


class ChunkTagResult(BaseModel):
    """Intermediate in-memory store per chunk after LLM phase"""
    chunk_id: str
    chunk_number: int
    tag_response: TagResponse


class ChunkTags(BaseModel):
    """Final output per chunk after post-processing"""
    chunk_id: str
    chunk_number: int
    new_tags: List[str]
    similar_tags: List[SimilarTag]
    reference_chunk_numbers: List[int]


class N4jChunkEdge(BaseModel):
    from_chunk_id: str
    to_chunk_id: str
    edge_name: str
    label: str
    weight: float


class ChunkDenseVectorScore(BaseModel):
    chunk_id: str
    score: float


class ChunkQuerySchema(BaseModel):
    chunk_id: str
    text: str
    weight: float


class VectorSimilarity(BaseModel):
    chunk_id: str
    text: str
    weight: float


class ChunkPrevNext(BaseModel):
    chunk_id: str
    text: str
    weight: float


class ChunkPrevNextVecSimilarity(BaseModel):
    chunk_id: str
    prev_chunk: Optional[ChunkPrevNext] = None
    next_chunk: Optional[ChunkPrevNext] = None
    vector_similar_chunks: Optional[List[VectorSimilarity]] = None
