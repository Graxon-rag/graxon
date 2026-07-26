from ..schemas.audio_model_schema import AudioModelCreateSchema, AudioModelGetSchema
from ..services.audio_model_service import AudioModelService
from app.constants.model_provider import AudioModelProvider
from app.utils.logger import logger
import uuid


class AudioModelHandler:
    def __init__(self, org_id: str):
        self.service = AudioModelService(org_id)

    async def create(self, data: AudioModelCreateSchema) -> AudioModelGetSchema:
        try:
            return await self.service.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create audio model", "error": str(e)})
            raise e

    async def create_multiple(self, audio_models: list[AudioModelCreateSchema]) -> bool:
        try:
            return await self.service.create_multiple(audio_models)
        except Exception as e:
            logger.error({"message": "Failed to create audio model", "error": str(e)})
            raise e

    async def get_by_provider(self, provider: AudioModelProvider) -> list[AudioModelGetSchema]:
        try:
            return await self.service.get_by_provider(provider)
        except Exception as e:
            logger.error({"message": "Failed to get audio model", "error": str(e)})
            raise e

    async def get(self, audio_model_id: uuid.UUID) -> AudioModelGetSchema | None:
        try:
            return await self.service.get(audio_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get audio model", "error": str(e)})
            raise e

    async def delete(self, audio_model_id: uuid.UUID) -> bool:
        try:
            return await self.service.delete(audio_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete audio model", "error": str(e)})
            raise e
