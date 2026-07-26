from ..schemas.video_model_schema import VideoModelCreateSchema, VideoModelGetSchema
from ..services.video_model_service import VideoModelService
from app.constants.model_provider import VideoModelProvider
from app.utils.logger import logger
import uuid


class VideoModelHandler:
    def __init__(self, org_id: str):
        self.service = VideoModelService(org_id)

    async def create(self, data: VideoModelCreateSchema) -> VideoModelGetSchema:
        try:
            return await self.service.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create video model", "error": str(e)})
            raise e

    async def create_multiple(self, video_models: list[VideoModelCreateSchema]) -> bool:
        try:
            return await self.service.create_multiple(video_models)
        except Exception as e:
            logger.error({"message": "Failed to create video model", "error": str(e)})
            raise e

    async def get(self, video_model_id: uuid.UUID) -> VideoModelGetSchema | None:
        try:
            return await self.service.get(video_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get video model", "error": str(e)})
            raise e

    async def get_by_provider(self, provider: VideoModelProvider) -> list[VideoModelGetSchema]:
        try:
            return await self.service.get_by_provider(provider)
        except Exception as e:
            logger.error({"message": "Failed to get video model", "error": str(e)})
            raise e

    async def delete(self, video_model_id: uuid.UUID) -> bool:
        try:
            return await self.service.delete(video_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete video model", "error": str(e)})
            raise e
