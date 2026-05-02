from ..schemas.embedding_model_schema import EmbeddingModelCreateSchema, EmbeddingModelGetSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import EmbeddingModel
from app.constants.model_provider import EmbeddingModelProvider
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class EmbeddingModelRepo:
    def __init__(self, org_id: str):
        self.db = GPostgresqlClient()
        self.org_id = org_id

    async def create(self, data: EmbeddingModelCreateSchema) -> EmbeddingModelGetSchema:
        try:
            async with self.db.get_session() as session:
                embedding_model = EmbeddingModel(
                    id=uuid.uuid4(),
                    org_id=self.org_id,
                    name=data.name,
                    provider=data.provider,
                    model_name=data.model_name,
                    model_id=data.model_id,
                    dimension=data.dimension,
                    description=data.description
                )
                session.add(embedding_model)
                await session.commit()
                return EmbeddingModelGetSchema(**embedding_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to create embedding model", "error": str(e)})
            raise e

    async def create_multiple(self, embedding_models: list[EmbeddingModelCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                embedding_model_models = [EmbeddingModel(**embedding_model.model_dump()) for embedding_model in embedding_models]
                session.add_all(embedding_model_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create embedding model", "error": str(e)})
            raise e

    async def get_all_embedding_model_by_provider(self, provider: EmbeddingModelProvider) -> list[EmbeddingModelGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(EmbeddingModel)
                stmt = stmt.where(EmbeddingModel.provider == provider)
                stmt = stmt.where(EmbeddingModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result = pg_result.scalars().all()
                return [EmbeddingModelGetSchema(**embedding_model.to_dict()) for embedding_model in result]
        except Exception as e:
            logger.error({"message": "Failed to get all embedding models", "error": str(e)})
            raise e

    async def get_embedding_model(self, embedding_model_id: uuid.UUID) -> EmbeddingModelGetSchema:
        try:
            async with self.db.get_session() as session:
                stmt = select(EmbeddingModel)
                stmt = stmt.where(EmbeddingModel.id == embedding_model_id)
                stmt = stmt.where(EmbeddingModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                embedding_model_model = pg_result.scalars().first()
                if embedding_model_model is None:
                    raise Exception(f"Embedding model with id {embedding_model_id} not found")
                return EmbeddingModelGetSchema(**embedding_model_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get embedding model", "error": str(e)})
            raise e

    async def delete(self, embedding_model_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                stmt = select(EmbeddingModel)
                stmt = stmt.where(EmbeddingModel.id == embedding_model_id)
                stmt = stmt.where(EmbeddingModel.org_id == self.org_id)

                pg_result = await session.execute(stmt)
                if pg_result is None:
                    raise Exception(f"Embedding model with id {embedding_model_id} not found")

                embedding_model_model = pg_result.scalars().first()
                await session.delete(embedding_model_model)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete embedding model", "error": str(e)})
            raise e
