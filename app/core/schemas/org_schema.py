from pydantic import BaseModel, Field
import datetime


class OrgCreateSchema(BaseModel):
    name: str = Field(
        description="The name of the organization",
    )
    description: str = Field(
        description="The description of the organization",
    )


class OrgGetSchema(BaseModel):
    id: str = Field(
        description="The id of the organization",
    )
    name: str = Field(
        description="The name of the organization",
    )
    description: str = Field(
        description="The description of the organization",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the organization",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the organization",
    )
