from pydantic import BaseModel, Field
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
