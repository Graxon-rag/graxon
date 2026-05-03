from pydantic import BaseModel, Field
from app.constants.document import DocumentStatus
import uuid
import datetime


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


class DocumentCreateSchema(BaseModel):
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

    status: DocumentStatus = Field(
        description="The status of the document",
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

    status: DocumentStatus = Field(
        description="The status of the document",
    )

    created_at: datetime.datetime = Field(
        description="The created at of the document",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the document",
    )


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
