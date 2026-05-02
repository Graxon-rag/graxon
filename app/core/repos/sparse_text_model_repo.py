from app.utils.logger import logger
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import SparseTextModel
from ..schemas.sparse_text_model_schema import SparseTextModelCreateSchema, SparseTextModelGetSchema
from sqlalchemy import select
import uuid


class SparseTextModelRepo:
    def __init__(self, org_id: str):
        self.org_id = org_id
        self.db = GPostgresqlClient()

    async def create_sparse_text_model(self, sparse_text_model: SparseTextModelCreateSchema) -> SparseTextModelGetSchema:
        try:
            async with self.db.get_session() as session:
                new_sparse_text_model = SparseTextModel(
                    org_id=self.org_id,
                    name=sparse_text_model.name,
                    provider=sparse_text_model.provider,
                    model=sparse_text_model.model,
                    description=sparse_text_model.description,
                    size_in_gb=sparse_text_model.size_in_gb,
                )
                session.add(new_sparse_text_model)
                await session.commit()
                return SparseTextModelGetSchema(**new_sparse_text_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to create sparse text model", "error": str(e)})
            raise e

    async def create_multiple_sparse_text_models(self, sparse_text_models: list[SparseTextModelCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                sparse_text_model_models = [SparseTextModel(**sparse_text_model.model_dump()) for sparse_text_model in sparse_text_models]
                session.add_all(sparse_text_model_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create sparse text model", "error": str(e)})
            raise e

    async def get_all_sparse_text_models(self) -> list[SparseTextModelGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(SparseTextModel)
                stmt = stmt.where(SparseTextModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result_list = list(pg_result.scalars().all())
                return [SparseTextModelGetSchema(**sparse_text_model.to_dict()) for sparse_text_model in result_list]
        except Exception as e:
            logger.error({"message": "Failed to get sparse text models", "error": str(e)})
            raise e

    async def get_sparse_text_model(self, sparse_text_model_id: uuid.UUID) -> SparseTextModelGetSchema:
        try:
            async with self.db.get_session() as session:
                sparse_text_model = await session.get(SparseTextModel, sparse_text_model_id)
                if sparse_text_model is None:
                    raise Exception(f"Sparse text model with id {sparse_text_model_id} not found")
                return SparseTextModelGetSchema(**sparse_text_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get sparse text model", "error": str(e)})
            raise e

    async def delete_sparse_text_model(self, sparse_text_model_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                sparse_text_model = await session.get(SparseTextModel, sparse_text_model_id)
                if sparse_text_model is None:
                    raise Exception(f"Sparse text model with id {sparse_text_model_id} not found")
                await session.delete(sparse_text_model)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete sparse text model", "error": str(e)})
            raise e
