from ..services.sparse_text_model_service import SparseTextModelService
from ..schemas.sparse_text_model_schema import SparseTextModelCreateSchema, SparseTextModelGetSchema
from app.utils.logger import logger
import uuid


class SparseTextModelHandler:
    def __init__(self, org_id: str):
        self.org_id = org_id
        self.service = SparseTextModelService(org_id=self.org_id)

    async def create_sparse_text_model(self, sparse_text_model: SparseTextModelCreateSchema) -> SparseTextModelGetSchema:
        try:
            return await self.service.create_sparse_text_model(sparse_text_model)
        except Exception as e:
            logger.error({"message": "Failed to create sparse text model", "error": str(e)})
            raise e

    async def create_multiple_sparse_text_models(self, sparse_text_models: list[SparseTextModelCreateSchema]):
        try:
            return await self.service.create_multiple_sparse_text_models(sparse_text_models)
        except Exception as e:
            logger.error({"message": "Failed to create sparse text model", "error": str(e)})
            raise e

    async def get_all_sparse_text_models(self) -> list[SparseTextModelGetSchema]:
        try:
            return await self.service.get_all_sparse_text_models()
        except Exception as e:
            logger.error({"message": "Failed to get sparse text models", "error": str(e)})
            raise e

    async def get_sparse_text_model(self, sparse_text_model_id: uuid.UUID) -> SparseTextModelGetSchema:
        try:
            return await self.service.get_sparse_text_model(sparse_text_model_id)
        except Exception as e:
            logger.error({"message": "Failed to get sparse text model", "error": str(e)})
            raise e

    async def delete_sparse_text_model(self, sparse_text_model_id: uuid.UUID) -> bool:
        try:
            return await self.service.delete_sparse_text_model(sparse_text_model_id)
        except Exception as e:
            logger.error({"message": "Failed to delete sparse text model", "error": str(e)})
            raise e
