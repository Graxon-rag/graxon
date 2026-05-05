from ..schemas.model_credential_schema import ModelCredentialGetSchema, ModelCredentialCreateSchema
from ..repos.model_credential_repo import ModelCredentialRepo
from ..libs.model_credential_lib import ModelCredentialLibs
from app.utils.logger import logger
import uuid


class ModelCredentialService:
    def __init__(self, org_id: str):
        self.repo = ModelCredentialRepo(org_id=org_id)
        self.org_id = org_id

    async def create_model_credential(self, model_credential: ModelCredentialCreateSchema, is_external_call: bool = True) -> ModelCredentialGetSchema:
        try:
            result = await self.repo.create(model_credential)
            if is_external_call:
                result.api_key = ModelCredentialLibs.get_hash_api_key(result.api_key)
            return result
        except Exception as e:
            logger.error({"message": "Failed to create model credential", "error": str(e)})
            raise e

    async def delete_model_credential(self, model_credential_id: uuid.UUID, is_external_call: bool = True) -> bool:
        try:
            return await self.repo.delete(model_credential_id)
        except Exception as e:
            logger.error({"message": "Failed to delete model credential", "error": str(e)})
            raise e

    async def get_model_credential(self, model_credential_id: uuid.UUID, is_external_call: bool = True) -> ModelCredentialGetSchema | None:
        try:
            result = await self.repo.get(model_credential_id)
            if is_external_call and result:
                result.api_key = ModelCredentialLibs.get_hash_api_key(result.api_key)
            return result
        except Exception as e:
            logger.error({"message": "Failed to get model credential", "error": str(e)})
            raise e

    async def get_all_model_credentials(self, provider: str, is_external_call: bool = True) -> list[ModelCredentialGetSchema]:
        try:
            results = await self.repo.get_all(provider)
            if is_external_call:
                for result in results:
                    result.api_key = ModelCredentialLibs.get_hash_api_key(result.api_key)
            return results
        except Exception as e:
            logger.error({"message": "Failed to get all model credentials", "error": str(e)})
            raise e
