from pydantic import BaseModel
from typing import Optional


class Chunk(BaseModel):
    chunk_id: str
    chunk_number: int
    text: str
    title: Optional[str] = None
    source: Optional[str] = None
    page_number: Optional[int] = None    
