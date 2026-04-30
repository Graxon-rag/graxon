from ..repos.reranker_repo import ReRankerRepo
from ..schemas.reranker_schema import ReRankerCreateSchema, ReRankerGetSchema
from app.utils.logger import logger
import uuid


class ReRankerService:
    def __init__(self, org_id: str):
        self.repo = ReRankerRepo(org_id)

    async def create_reranker(self, reranker: ReRankerCreateSchema) -> ReRankerGetSchema:
        try:
            return await self.repo.create_reranker(reranker)
        except Exception as e:
            logger.error({"message": "Failed to create reranker", "error": str(e)})
            raise e

    async def create_multiple_rerankers(self, rerankers: list[ReRankerCreateSchema]):
        try:
            return await self.repo.create_multiple(rerankers)
        except Exception as e:
            logger.error({"message": "Failed to create reranker", "error": str(e)})
            raise e

    async def get_reranker(self, reranker_id: uuid.UUID) -> ReRankerGetSchema:
        try:
            return await self.repo.get_reranker(reranker_id)
        except Exception as e:
            logger.error({"message": "Failed to get reranker", "error": str(e)})
            raise e

    async def get_all_rerankers(self) -> list[ReRankerGetSchema]:
        try:
            return await self.repo.get_all_rerankers()
        except Exception as e:
            logger.error({"message": "Failed to get rerankers", "error": str(e)})
            raise e

    async def delete_reranker(self, reranker_id: uuid.UUID) -> bool:
        try:
            return await self.repo.delete_reranker(reranker_id)
        except Exception as e:
            logger.error({"message": "Failed to delete reranker", "error": str(e)})
            raise e
