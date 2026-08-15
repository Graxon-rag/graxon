from app.constants.document import DocumentStatus
from .common_schema import PaginationSchema
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import datetime
import uuid


class DocumentUploadSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the document",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the document",
    )
    id: uuid.UUID = Field(
        description="The id of the document",
    )
    name: str = Field(
        description="The file name of the document",
    )
    type: str = Field(
        description="The file type of the document",
    )
    size: int | None = Field(
        default=None,
        description="The file size of the document",
    )
    is_ocr_needed: bool = Field(
        default=False,
        description="True if OCR is needed",
    )


class DocumentUploadResponseSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the document",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the document",
    )
    id: uuid.UUID = Field(
        description="The id of the document",
    )
    bucket: str = Field(
        description="The bucket of the document",
    )
    key: str = Field(
        description="The key of the document",
    )
    size: int | None = Field(
        default=None,
        description="The file size of the document",
    )

    signed_url: str = Field(
        description="The signed url of the document",
    )

    is_ocr_needed: bool = Field(
        default=False,
        description="True if OCR is needed",
    )


class DocumentGetSignedUrlSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the document",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the document",
    )
    bucket: str = Field(
        description="The bucket of the document",
    )
    key: str = Field(
        description="The key of the document",
    )


class DocumentCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the document",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the document",
    )
    id: uuid.UUID = Field(
        description="The id of the document",
    )
    readable_id: str = Field(
        description="The readable id of the document",
    )
    name: str = Field(
        description="The file name of the document",
    )
    type: str = Field(
        description="The file type of the document",
    )
    bucket: str = Field(
        description="The bucket of the document",
    )
    key: str = Field(
        description="The key of the document",
    )

    size: int | None = Field(
        default=None,
        description="The file size of the document",
    )

    status: DocumentStatus = Field(
        description="The status of the document",
    )

    is_ocr_needed: bool = Field(
        default=False,
        description="True if OCR is needed",
    )


class DocumentGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the document",
    )
    org_id: str = Field(
        description="The organization id of the document",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the document",
    )
    readable_id: str = Field(
        description="The readable id of the document",
    )
    name: str = Field(
        description="The file name of the document",
    )
    type: str = Field(
        description="The file type of the document",
    )
    bucket: str = Field(
        description="The bucket of the document",
    )
    key: str = Field(
        description="The key of the document",
    )
    size: int | None = Field(
        default=None,
        description="The file size of the document",
    )

    status: DocumentStatus = Field(
        description="The status of the document",
    )

    is_ocr_needed: bool = Field(
        default=False,
        description="True if OCR is needed",
    )

    created_at: datetime.datetime = Field(
        description="The created at of the document",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the document",
    )


class SortField(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"
    SIZE = "size"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SizeOp(str, Enum):
    GT = ">"
    LT = "<"
    EQ = "="


class DocumentQueryParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)
    status: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None  # Specific extension like "pdf", "png", "py"
    types: Optional[list[str]] = None  # Category group like [".pdf", ".doc"]
    size: Optional[int] = None  # Size in bytes
    size_op: Optional[SizeOp] = SizeOp.EQ
    sort_by: SortField = SortField.CREATED_AT  # No Optional[]
    sort_order: SortOrder = SortOrder.DESC     # No Optional[]


class DocumentListSchema(BaseModel):
    data: list[DocumentGetSchema]
    pagination: Optional[PaginationSchema] = None


class DocumentStatusMQSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the document",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the document",
    )
    id: uuid.UUID = Field(
        description="The id of the document",
    )
    status: DocumentStatus = Field(
        description="The status of the document",
    )


class DocumentMultipartUploadPartSchema(BaseModel):
    etag: str = Field(
        description="The etag of the document",
    )
    part_number: int = Field(
        description="The part number of the document",
    )


class PresignedUrlRequestSchema(BaseModel):
    upload_id: str
    key: str
    part_number: int


class CompleteMultipartUploadSchema(BaseModel):
    upload_id: str
    key: str
    file_name: str
    size: int | None = None
    is_ocr_needed: bool = False
    parts: list[DocumentMultipartUploadPartSchema]
