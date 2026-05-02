from ..schemas.llm_model_schema import LLMModelCreateSchema, LLMModelGetSchema
from ..repos.llm_model_repo import LLMModelRepo
from app.utils.logger import logger
from app.constants.model_provider import LLMModelProvider
import uuid


class LLMModelService:
    def __init__(self, org_id: str):
        self.repo = LLMModelRepo(org_id)

    async def create(self, data: LLMModelCreateSchema) -> LLMModelGetSchema:
        try:
            return await self.repo.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create LLM model", "error": str(e)})
            raise e

    async def create_multiple(self, llm_models: list[LLMModelCreateSchema]) -> bool:
        try:
            return await self.repo.create_multiple(llm_models)
        except Exception as e:
            logger.error({"message": "Failed to create LLM model", "error": str(e)})
            raise e

    async def get_all_llm_model_by_provider(self, provider: LLMModelProvider) -> list[LLMModelGetSchema]:
        try:
            return await self.repo.get_all_llm_model_by_provider(provider)
        except Exception as e:
            logger.error({"message": "Failed to get all LLM models", "error": str(e)})
            raise e

    async def get_llm_model(self, llm_model_id: uuid.UUID) -> LLMModelGetSchema:
        try:
            return await self.repo.get_llm_model(llm_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get LLM model", "error": str(e)})
            raise e

    async def delete(self, llm_model_id: uuid.UUID) -> bool:
        try:
            return await self.repo.delete(llm_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete LLM model", "error": str(e)})
            raise e
