from ..schemas.audio_model_schema import AudioModelCreateSchema, AudioModelGetSchema
from app.constants.model_provider import AudioModelProvider
from ..repos.audio_model_repo import AudioModelRepo
from app.utils.logger import logger
import uuid


class AudioModelService:
    def __init__(self, org_id: str):
        self.repo = AudioModelRepo(org_id)

    async def create(self, data: AudioModelCreateSchema) -> AudioModelGetSchema:
        try:
            return await self.repo.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create audio model", "error": str(e)})
            raise e

    async def create_multiple(self, audio_models: list[AudioModelCreateSchema]) -> bool:
        try:
            return await self.repo.create_multiple(audio_models)
        except Exception as e:
            logger.error({"message": "Failed to create audio model", "error": str(e)})
            raise e

    async def get(self, audio_model_id: uuid.UUID) -> AudioModelGetSchema | None:
        try:
            return await self.repo.get(audio_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get audio model", "error": str(e)})
            raise e

    async def get_by_provider(self, provider: AudioModelProvider) -> list[AudioModelGetSchema]:
        try:
            return await self.repo.get_by_provider(provider)
        except Exception as e:
            logger.error({"message": "Failed to get audio model", "error": str(e)})
            raise e

    async def delete(self, audio_model_id: uuid.UUID) -> bool:
        try:
            return await self.repo.delete(audio_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete audio model", "error": str(e)})
            raise e
