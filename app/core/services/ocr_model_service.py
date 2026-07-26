from ..schemas.ocr_model_schema import OCRModelCreateSchema, OCRModelGetSchema
from app.constants.model_provider import OCRModelProvider
from ..repos.ocr_model_repo import OCRModelRepo
from app.utils.logger import logger
import uuid


class OCRModelService:
    def __init__(self, org_id: str):
        self.repo = OCRModelRepo(org_id)

    async def create(self, data: OCRModelCreateSchema) -> OCRModelGetSchema:
        try:
            return await self.repo.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create OCR model", "error": str(e)})
            raise e

    async def create_multiple(self, ocr_models: list[OCRModelCreateSchema]) -> bool:
        try:
            return await self.repo.create_multiple(ocr_models)
        except Exception as e:
            logger.error({"message": "Failed to create OCR model", "error": str(e)})
            raise e

    async def get_by_provider(self, provider: OCRModelProvider) -> list[OCRModelGetSchema]:
        try:
            return await self.repo.get_by_provider(provider)
        except Exception as e:
            logger.error({"message": "Failed to get OCR model", "error": str(e)})
            raise e

    async def get(self, ocr_model_id: uuid.UUID) -> OCRModelGetSchema | None:
        try:
            return await self.repo.get(ocr_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get OCR model", "error": str(e)})
            raise e

    async def delete(self, ocr_model_id: uuid.UUID) -> bool:
        try:
            return await self.repo.delete(ocr_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete OCR model", "error": str(e)})
            raise e
