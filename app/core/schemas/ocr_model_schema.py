from app.constants.model_provider import OCRModelProvider
from pydantic import BaseModel, Field
import datetime
import uuid


class OCRModelCreateSchema(BaseModel):
    org_id: str = Field(
        description="The organization id of the OCR model",
    )
    name: str = Field(
        description="The name of the OCR model",
    )
    provider: OCRModelProvider = Field(
        description="The provider of the OCR model",
    )
    model_name: str = Field(
        description="The model name of the OCR model",
    )
    model_id: str = Field(
        description="The model id of the OCR model",
    )
    description: str = Field(
        description="The description of the OCR model",
    )


class OCRModelGetSchema(BaseModel):
    id: uuid.UUID = Field(
        description="The id of the OCR model",
    )
    org_id: str = Field(
        description="The organization id of the OCR model",
    )
    name: str = Field(
        description="The name of the OCR model",
    )
    provider: OCRModelProvider = Field(
        description="The provider of the OCR model",
    )
    model_name: str = Field(
        description="The model name of the OCR model",
    )
    model_id: str = Field(
        description="The model id of the OCR model",
    )
    description: str = Field(
        description="The description of the OCR model",
    )
    created_at: datetime.datetime = Field(
        description="The created at of the OCR model",
    )
    updated_at: datetime.datetime = Field(
        description="The updated at of the OCR model",
    )
