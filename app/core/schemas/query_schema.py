from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid


class QueryType(str, Enum):
    QUICK = "quick"
    SMART = "smart"
    EXPERT = "expert"


class QueryDepth(str, Enum):
    STANDARD = "standard"
    ADVANCED = "advanced"


class GQuery(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    document_id: Optional[uuid.UUID] = Field(default=None, description="Optional document id")
    query_type: QueryType = Field(default=QueryType.SMART, description="Query type")
    query_depth: QueryDepth = Field(default=QueryDepth.STANDARD, description="Query depth")
