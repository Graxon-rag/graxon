from pydantic import BaseModel, Field
import uuid
import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class DocumentUploadSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the document",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the document",
    )
    name: str = Field(
        description="The file name of the document",
    )
    type: str = Field(
        description="The file type of the document",
    )


class DocumentUploadResponseSchema(BaseModel):
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

    signed_url: str = Field(
        description="The signed url of the document",
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
