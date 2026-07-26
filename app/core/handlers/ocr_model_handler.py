from ..schemas.ocr_model_schema import OCRModelCreateSchema, OCRModelGetSchema
from app.constants.model_provider import OCRModelProvider
from ..services.ocr_model_service import OCRModelService
from app.utils.logger import logger
import uuid


class OCRModelHandler:
    def __init__(self, org_id: str):
        self.service = OCRModelService(org_id)

    async def create(self, data: OCRModelCreateSchema):
        try:
            return await self.service.create(data)
        except Exception as e:
            logger.error(e)
            return

    async def create_multiple(self, ocr_models: list[OCRModelCreateSchema]):
        try:
            return await self.service.create_multiple(ocr_models)
        except Exception as e:
            logger.error(e)
            return

    async def get_by_provider(self, provider: OCRModelProvider):
        try:
            return await self.service.get_by_provider(provider)
        except Exception as e:
            logger.error(e)
            return

    async def get(self, ocr_model_id: uuid.UUID):
        try:
            return await self.service.get(ocr_model_id)
        except Exception as e:
            logger.error(e)
            return

    async def delete(self, ocr_model_id: uuid.UUID):
        try:
            return await self.service.delete(ocr_model_id)
        except Exception as e:
            logger.error(e)
            return
