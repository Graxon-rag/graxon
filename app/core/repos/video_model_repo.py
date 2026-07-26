from ..schemas.video_model_schema import VideoModelCreateSchema, VideoModelGetSchema
from ..databases.postgresql.client import GPostgresqlClient
from app.constants.model_provider import VideoModelProvider
from ..databases.postgresql.models import VideoModel
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class VideoModelRepo:
    def __init__(self, org_id: str):
        self.db = GPostgresqlClient()
        self.org_id = org_id

    async def create(self, data: VideoModelCreateSchema) -> VideoModelGetSchema:
        try:
            async with self.db.get_session() as session:
                new_video_model = VideoModel(
                    org_id=self.org_id,
                    name=data.name,
                    provider=data.provider,
                    model_name=data.model_name,
                    model_id=data.model_id,
                    description=data.description,
                    model_metadata=data.model_metadata or {}
                )
                session.add(new_video_model)
                await session.commit()
                get_result = await self.get(new_video_model.id)
                if get_result is None:
                    raise Exception(f"Video model with id {new_video_model.id} not found")
                return get_result
        except Exception as e:
            logger.error({"message": "Failed to create video model", "error": str(e)})
            raise e

    async def create_multiple(self, video_models: list[VideoModelCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                video_model_models = [VideoModel(**video_model.model_dump()) for video_model in video_models]
                session.add_all(video_model_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create video model", "error": str(e)})
            raise e

    async def get(self, video_model_id: uuid.UUID) -> VideoModelGetSchema | None:
        try:
            async with self.db.get_session() as session:
                stmt = select(VideoModel)
                stmt = stmt.where(VideoModel.id == video_model_id)
                stmt = stmt.where(VideoModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                video_model_model = pg_result.scalars().first()
                if video_model_model is None:
                    raise Exception(f"Video model with id {video_model_id} not found")
                return VideoModelGetSchema(**video_model_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get video model", "error": str(e)})
            raise e

    async def get_by_provider(self, provider: VideoModelProvider) -> list[VideoModelGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(VideoModel)
                stmt = stmt.where(VideoModel.provider == provider)
                stmt = stmt.where(VideoModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result = pg_result.scalars().all()
                return [VideoModelGetSchema(**video_model.to_dict()) for video_model in result]
        except Exception as e:
            logger.error({"message": "Failed to get video model", "error": str(e)})
            raise e

    async def delete(self, video_model_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                stmt = select(VideoModel)
                stmt = stmt.where(VideoModel.id == video_model_id)
                stmt = stmt.where(VideoModel.org_id == self.org_id)

                pg_result = await session.execute(stmt)
                if pg_result is None:
                    raise Exception(f"Video model with id {video_model_id} not found")

                video_model_model = pg_result.scalars().first()
                await session.delete(video_model_model)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete video model", "error": str(e)})
            raise e
