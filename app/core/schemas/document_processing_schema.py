from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class ProcessingStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DocumentProcessingBase(BaseModel):
    document_id: uuid.UUID
    status: ProcessingStatus = ProcessingStatus.PENDING
    last_file_chunk_number: int = Field(default=-1, description="Highest chunk number successfully processed")
    next_rag_start_index: int = Field(default=0, description="Offset cursor for the next chunk")
    next_start_row: int = Field(default=0)
    next_start_object: int = Field(default=0)
    next_start_unit: int = Field(default=0)
    next_start_page: int = Field(default=0)
    error_message: Optional[str] = None


class DocumentProcessingCreateSchema(DocumentProcessingBase):
    pass


class DocumentProcessingUpdateSchema(BaseModel):
    status: Optional[ProcessingStatus] = None
    last_file_chunk_number: Optional[int] = None
    next_rag_start_index: Optional[int] = None
    next_start_row: int = Field(default=0)
    next_start_object: int = Field(default=0)
    next_start_unit: int = Field(default=0)
    next_start_page: int = Field(default=0)
    error_message: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentProcessingGetSchema(DocumentProcessingBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
