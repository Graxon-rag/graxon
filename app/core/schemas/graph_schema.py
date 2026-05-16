from pydantic import BaseModel, Field
from typing import Optional


class Pagination(BaseModel):
    current_page: int
    current_limit: int
    total_pages: int
    total_items: int
    has_next: bool
    has_previous: bool


class N4jTagSchema(BaseModel):
    id: str
    type: str
    value: str
    frequency: int


class N4jEntitySchema(BaseModel):
    id: str
    type: str
    value: str
    frequency: int


class N4jConceptSchema(BaseModel):
    id: str
    type: str
    value: str
    frequency: int


class N4jKeywordSchema(BaseModel):
    id: str
    type: str
    value: str
    frequency: int


class N4jPhraseSchema(BaseModel):
    id: str
    type: str
    value: str
    frequency: int


class N4jChunkEdgeCommonSchema(BaseModel):
    chunk_id: str
    type: str
    frequency: int
    weight: float


class N4jCommonEdgeChunksSchema(BaseModel):
    id: str
    type: str
    value: str
    frequency: int
    chunks_ids: Optional[list[N4jChunkEdgeCommonSchema]] = None


class N4jChunkSchema(BaseModel):
    org_id: Optional[str] = None
    project_id: Optional[str] = None
    document_id: str
    document_readable_id: str
    id: str
    type: Optional[str] = "Chunk"
    chunk_number: int
    text: str
    page_number: Optional[int] = None
    title: Optional[str] = None
    source: Optional[str] = None


class GN4jTagGetSchema(BaseModel):
    data: list[N4jTagSchema]
    pagination: Pagination


class GN4jEntityGetSchema(BaseModel):
    data: list[N4jEntitySchema]
    pagination: Pagination


class GN4jConceptGetSchema(BaseModel):
    data: list[N4jConceptSchema]
    pagination: Pagination


class GN4jKeywordGetSchema(BaseModel):
    data: list[N4jKeywordSchema]
    pagination: Pagination


class GN4jPhraseGetSchema(BaseModel):
    data: list[N4jPhraseSchema]
    pagination: Pagination


class GN4jChunkGetSchema(BaseModel):
    data: list[N4jChunkSchema]
    pagination: Pagination
