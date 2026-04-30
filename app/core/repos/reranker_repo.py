from ..schemas.reranker_schema import ReRankerCreateSchema, ReRankerGetSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import ReRankerModel
from app.utils.logger import logger
from sqlalchemy import select, func
import uuid


class ReRankerRepo:
    def __init__(self, org_id: str):
        self.db = GPostgresqlClient()
        self.org_id = org_id


    async def create_reranker(self, reranker: ReRankerCreateSchema) -> ReRankerGetSchema:
        try:
            async with self.db.get_session() as session:
                new_reranker = ReRankerModel(
                    org_id=self.org_id,
                    name=reranker.name,
                    provider=reranker.provider,
                    model=reranker.model,
                    description=reranker.description,
                    size_in_gb=reranker.size_in_gb,
                )
                session.add(new_reranker)
                await session.commit()
                return ReRankerGetSchema(**new_reranker.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to create reranker", "error": str(e)})
            raise e

    async def create_multiple(self, rerankers: list[ReRankerCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                reranker_models = [ReRankerModel(**reranker.model_dump()) for reranker in rerankers]
                session.add_all(reranker_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create reranker", "error": str(e)})
            raise e


    async def get_reranker(self, reranker_id: uuid.UUID) -> ReRankerGetSchema:
        try:
            async with self.db.get_session() as session:
                reranker = await session.get(ReRankerModel, reranker_id)
                if reranker is None:
                    raise Exception(f"Reranker with id {reranker_id} not found")
                return ReRankerGetSchema(**reranker.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get reranker", "error": str(e)})
            raise e


    async def get_all_rerankers(self) -> list[ReRankerGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(ReRankerModel)
                stmt = stmt.where(ReRankerModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result_list = list(pg_result.scalars().all())
                return [ReRankerGetSchema(**reranker.to_dict()) for reranker in result_list]
        except Exception as e:
            logger.error({"message": "Failed to get rerankers", "error": str(e)})
            raise e

    async def delete_reranker(self, reranker_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                reranker = await session.get(ReRankerModel, reranker_id)
                if reranker is None:
                    raise Exception(f"Reranker with id {reranker_id} not found")
                await session.delete(reranker)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete reranker", "error": str(e)})
            raise e
