from ..schemas.embedding_model_schema import EmbeddingModelCreateSchema, EmbeddingModelGetSchema
from ..services.embedding_model_service import EmbeddingModelService
from app.constants.model_provider import EmbeddingModelProvider
from app.utils.logger import logger
import uuid


class EmbeddingModelHandler:
    def __init__(self, org_id: str):
        self.service = EmbeddingModelService(org_id)

    async def create(self, data: EmbeddingModelCreateSchema) -> EmbeddingModelGetSchema:
        try:
            return await self.service.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create embedding model", "error": str(e)})
            raise e

    async def create_multiple(self, embedding_models: list[EmbeddingModelCreateSchema]) -> bool:
        try:
            return await self.service.create_multiple(embedding_models)
        except Exception as e:
            logger.error({"message": "Failed to create embedding model", "error": str(e)})
            raise e

    async def get_embedding_model(self, embedding_model_id: uuid.UUID) -> EmbeddingModelGetSchema:
        try:
            return await self.service.get_embedding_model(embedding_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get embedding model", "error": str(e)})
            raise e

    async def get_all_embedding_model_by_provider(self, provider: EmbeddingModelProvider) -> list[EmbeddingModelGetSchema]:
        try:
            return await self.service.get_all_embedding_model_by_provider(provider)
        except Exception as e:
            logger.error({"message": "Failed to get all embedding models", "error": str(e)})
            raise e

    async def delete(self, embedding_model_id: uuid.UUID) -> bool:
        try:
            return await self.service.delete(embedding_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete embedding model", "error": str(e)})
            raise e
