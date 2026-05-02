from ..schemas.model_credential_schema import ModelCredentialGetSchema, ModelCredentialCreateSchema
from ..repos.model_credential_repo import ModelCredentialRepo
from app.utils.logger import logger
import uuid


class ModelCredentialService:
    def __init__(self, org_id: str):
        self.repo = ModelCredentialRepo(org_id=org_id)
        self.org_id = org_id

    async def create_model_credential(self, model_credential: ModelCredentialCreateSchema) -> ModelCredentialGetSchema:
        try:
            return await self.repo.create(model_credential)
        except Exception as e:
            logger.error({"message": "Failed to create model credential", "error": str(e)})
            raise e

    async def delete_model_credential(self, model_credential_id: uuid.UUID) -> bool:
        try:
            return await self.repo.delete(model_credential_id)
        except Exception as e:
            logger.error({"message": "Failed to delete model credential", "error": str(e)})
            raise e

    async def get_model_credential(self, model_credential_id: uuid.UUID) -> ModelCredentialGetSchema | None:
        try:
            return await self.repo.get(model_credential_id)
        except Exception as e:
            logger.error({"message": "Failed to get model credential", "error": str(e)})
            raise e

    async def get_all_model_credentials(self, provider: str) -> list[ModelCredentialGetSchema]:
        try:
            return await self.repo.get_all(provider)
        except Exception as e:
            logger.error({"message": "Failed to get all model credentials", "error": str(e)})
            raise e
