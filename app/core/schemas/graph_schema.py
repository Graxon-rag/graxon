from pydantic import BaseModel, Field


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


class GN4jTagGetSchema(BaseModel):
    data: list[N4jTagSchema]
    pagination: Pagination


class GN4jEntityGetSchema(BaseModel):
    data: list[N4jEntitySchema]
    pagination: Pagination


class GN4jConceptGetSchema(BaseModel):
    data: list[N4jConceptSchema]
    pagination: Pagination
