from ..services.reranker_service import ReRankerService
from app.utils.logger import logger
from ..schemas.reranker_schema import ReRankerCreateSchema, ReRankerGetSchema
import uuid


class ReRankerHandler:
    def __init__(self, org_id: str):
        self.service = ReRankerService(org_id)

    async def create_reranker(self, reranker: ReRankerCreateSchema) -> ReRankerGetSchema:
        try:
            return await self.service.create_reranker(reranker)
        except Exception as e:
            logger.error({"message": "Failed to create reranker", "error": str(e)})
            raise e

    async def create_multiple_rerankers(self, rerankers: list[ReRankerCreateSchema]):
        try:
            return await self.service.create_multiple_rerankers(rerankers)
        except Exception as e:
            logger.error({"message": "Failed to create reranker", "error": str(e)})
            raise e

    async def get_reranker(self, reranker_id: uuid.UUID) -> ReRankerGetSchema:
        try:
            return await self.service.get_reranker(reranker_id)
        except Exception as e:
            logger.error({"message": "Failed to get reranker", "error": str(e)})
            raise e

    async def get_all_rerankers(self) -> list[ReRankerGetSchema]:
        try:
            return await self.service.get_all_rerankers()
        except Exception as e:
            logger.error({"message": "Failed to get rerankers", "error": str(e)})
            raise e

    async def delete_reranker(self, reranker_id: uuid.UUID) -> bool:
        try:
            return await self.service.delete_reranker(reranker_id)
        except Exception as e:
            logger.error({"message": "Failed to delete reranker", "error": str(e)})
            raise e
