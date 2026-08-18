from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
import datetime
import uuid


class WebhookCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the Webhook",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the Webhook",
    )
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="The id of the document",
    )
    name: str = Field(
        description="The name of the Webhook",
    )
    url: str = Field(
        description="The url of the Webhook",
    )
    token: str = Field(
        description="The token of the Webhook, will be pass in header 'X-GRAXON-TOKEN' to the request",
    )


class WebhookGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the Webhook",
    )
    org_id: str = Field(
        description="The organization id of the Webhook",
    )
    project_id: uuid.UUID = Field(
        description="The project id of the Webhook",
    )
    name: str = Field(
        description="The name of the Webhook",
    )
    url: str = Field(
        description="The url of the Webhook",
    )
    token: str = Field(
        description="The token of the Webhook, will be pass in header 'X-GRAXON-TOKEN' to the request",
    )
    created_at: datetime.datetime = Field(
            description="The created at of the organization",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the organization",
    )


class WebhookEventEnum(str, Enum):
    DOCUMENT_PENDING = "document.pending"
    DOCUMENT_QUEUED = "document.queued"
    DOCUMENT_PROCESSING = "document.processing"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_FAILED = "document.failed"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_VECTOR_SIMILARITY_PROCESSED = "document.vector_similarity.processed"
    DOCUMENT_VECTOR_SIMILARITY_FAILED = "document.vector_similarity.failed"


class WebhookEventParams(BaseModel):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="The id of the event object",
    )
    event: WebhookEventEnum
    data: Optional[Dict[Any, Any]] = None
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        description="The created at of the event object",
    )


class WebhookSendParams(BaseModel):
    event_data: WebhookEventParams
    webhooks: List[WebhookGetSchema] = Field(
        default=[],
        description="The list of webhooks to send the event to",
    )
