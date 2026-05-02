from ..databases.postgresql.client import GPostgresqlClient
from app.constants.model_provider import LLMModelProvider
from ..databases.postgresql.models import LLMModel
from ..schemas.llm_model_schema import LLMModelCreateSchema, LLMModelGetSchema
from sqlalchemy import select
from app.utils.logger import logger
import uuid


class LLMModelRepo:
    def __init__(self, org_id: str):
        self.db = GPostgresqlClient()
        self.org_id = org_id

    async def create(self, data: LLMModelCreateSchema) -> LLMModelGetSchema:
        try:
            async with self.db.get_session() as session:
                new_llm_model = LLMModel(
                    org_id=self.org_id,
                    name=data.name,
                    provider=data.provider,
                    model_name=data.model_name,
                    model_id=data.model_id,
                    description=data.description,
                )
                session.add(new_llm_model)
                await session.commit()
                return LLMModelGetSchema(**new_llm_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to create LLM model", "error": str(e)})
            raise e

    async def create_multiple(self, llm_models: list[LLMModelCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                llm_model_models = [LLMModel(**llm_model.model_dump()) for llm_model in llm_models]
                session.add_all(llm_model_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create LLM model", "error": str(e)})
            raise e

    async def get_llm_model(self, llm_model_id: uuid.UUID) -> LLMModelGetSchema:
        try:
            async with self.db.get_session() as session:
                stmt = select(LLMModel)
                stmt = stmt.where(LLMModel.id == llm_model_id)
                stmt = stmt.where(LLMModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                llm_model_model = pg_result.scalars().first()
                if llm_model_model is None:
                    raise Exception(f"LLM model with id {llm_model_id} not found")
                return LLMModelGetSchema(**llm_model_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get LLM model", "error": str(e)})
            raise e

    async def get_all_llm_model_by_provider(self, provider: LLMModelProvider) -> list[LLMModelGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(LLMModel)
                stmt = stmt.where(LLMModel.provider == provider)
                stmt = stmt.where(LLMModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result = pg_result.scalars().all()
                return [LLMModelGetSchema(**llm_model.to_dict()) for llm_model in result]
        except Exception as e:
            logger.error({"message": "Failed to get all LLM models", "error": str(e)})
            raise e

    async def delete(self, llm_model_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                stmt = select(LLMModel)
                stmt = stmt.where(LLMModel.id == llm_model_id)
                stmt = stmt.where(LLMModel.org_id == self.org_id)

                pg_result = await session.execute(stmt)
                if pg_result is None:
                    raise Exception(f"LLM model with id {llm_model_id} not found")

                llm_model_model = pg_result.scalars().first()
                await session.delete(llm_model_model)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete LLM model", "error": str(e)})
            raise e
