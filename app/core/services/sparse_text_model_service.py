from ..schemas.sparse_text_model_schema import SparseTextModelCreateSchema, SparseTextModelGetSchema
from ..repos.sparse_text_model_repo import SparseTextModelRepo
from app.utils.logger import logger
import uuid


class SparseTextModelService:
    def __init__(self, org_id: str):
        self.org_id = org_id
        self.repo = SparseTextModelRepo(org_id=self.org_id)

    async def create_sparse_text_model(self, sparse_text_model: SparseTextModelCreateSchema) -> SparseTextModelGetSchema:
        try:
            return await self.repo.create_sparse_text_model(sparse_text_model)
        except Exception as e:
            logger.error({"message": "Failed to create sparse text model", "error": str(e)})
            raise e

    async def create_multiple_sparse_text_models(self, sparse_text_models: list[SparseTextModelCreateSchema]):
        try:
            return await self.repo.create_multiple_sparse_text_models(sparse_text_models)
        except Exception as e:
            logger.error({"message": "Failed to create sparse text model", "error": str(e)})
            raise e

    async def get_all_sparse_text_models(self) -> list[SparseTextModelGetSchema]:
        try:
            return await self.repo.get_all_sparse_text_models()
        except Exception as e:
            logger.error({"message": "Failed to get sparse text models", "error": str(e)})
            raise e

    async def get_sparse_text_model(self, sparse_text_model_id: uuid.UUID) -> SparseTextModelGetSchema:
        try:
            return await self.repo.get_sparse_text_model(sparse_text_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get sparse text model", "error": str(e)})
            raise e

    async def delete_sparse_text_model(self, sparse_text_model_id: uuid.UUID) -> bool:
        try:
            return await self.repo.delete_sparse_text_model(sparse_text_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete sparse text model", "error": str(e)})
            raise e
