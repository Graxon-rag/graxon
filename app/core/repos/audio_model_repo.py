from ..schemas.audio_model_schema import AudioModelCreateSchema, AudioModelGetSchema
from ..databases.postgresql.client import GPostgresqlClient
from app.constants.model_provider import AudioModelProvider
from ..databases.postgresql.models import AudioModel
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class AudioModelRepo:
    def __init__(self, org_id: str):
        self.db = GPostgresqlClient()
        self.org_id = org_id

    async def create(self, data: AudioModelCreateSchema) -> AudioModelGetSchema:
        try:
            async with self.db.get_session() as session:
                new_audio_model = AudioModel(
                    org_id=self.org_id,
                    name=data.name,
                    provider=data.provider,
                    model_name=data.model_name,
                    model_id=data.model_id,
                    description=data.description,
                    model_metadata=data.model_metadata or {}
                )
                session.add(new_audio_model)
                await session.commit()
                get_result = await self.get(new_audio_model.id)
                if get_result is None:
                    raise Exception(f"Audio model with id {new_audio_model.id} not found")
                return get_result
        except Exception as e:
            logger.error({"message": "Failed to create audio model", "error": str(e)})
            raise e

    async def create_multiple(self, audio_models: list[AudioModelCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                audio_model_models = [AudioModel(**audio_model.model_dump()) for audio_model in audio_models]
                session.add_all(audio_model_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create audio model", "error": str(e)})
            raise e

    async def get(self, audio_model_id: uuid.UUID) -> AudioModelGetSchema | None:
        try:
            async with self.db.get_session() as session:
                stmt = select(AudioModel)
                stmt = stmt.where(AudioModel.id == audio_model_id)
                stmt = stmt.where(AudioModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                audio_model_model = pg_result.scalars().first()
                if audio_model_model is None:
                    raise Exception(f"Audio model with id {audio_model_id} not found")
                return AudioModelGetSchema(**audio_model_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get audio model", "error": str(e)})
            raise e

    async def get_by_provider(self, provider: AudioModelProvider) -> list[AudioModelGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(AudioModel)
                stmt = stmt.where(AudioModel.provider == provider)
                stmt = stmt.where(AudioModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result = pg_result.scalars().all()
                return [AudioModelGetSchema(**audio_model.to_dict()) for audio_model in result]
        except Exception as e:
            logger.error({"message": "Failed to get audio model", "error": str(e)})
            raise e

    async def delete(self, audio_model_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                stmt = select(AudioModel)
                stmt = stmt.where(AudioModel.id == audio_model_id)
                stmt = stmt.where(AudioModel.org_id == self.org_id)

                pg_result = await session.execute(stmt)
                if pg_result is None:
                    raise Exception(f"Audio model with id {audio_model_id} not found")

                audio_model_model = pg_result.scalars().first()
                await session.delete(audio_model_model)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete audio model", "error": str(e)})
            raise e
