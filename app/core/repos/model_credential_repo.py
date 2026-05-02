from ..schemas.model_credential_schema import ModelCredentialGetSchema, ModelCredentialCreateSchema
from ..databases.postgresql.models import ModelCredential
from ..databases.postgresql.client import GPostgresqlClient
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class ModelCredentialRepo:
    def __init__(self, org_id: str):
        self.org_id = org_id
        self.client = GPostgresqlClient()

    async def create(self, model_credential_input: ModelCredentialCreateSchema) -> ModelCredentialGetSchema:
        try:
            async with self.client.get_session() as session:
                model_credential = ModelCredential(
                    org_id=self.org_id,
                    name=model_credential_input.name,
                    description=model_credential_input.description,
                    provider=model_credential_input.provider,
                    api_key=model_credential_input.api_key
                )
                session.add(model_credential)
                await session.commit()
                return ModelCredentialGetSchema(**model_credential.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to create model credential", "error": str(e)})
            raise e

    async def get(self, model_credential_id: uuid.UUID) -> ModelCredentialGetSchema | None:
        try:
            async with self.client.get_session() as session:
                stmt = select(ModelCredential)
                stmt = stmt.where(ModelCredential.id == model_credential_id)
                stmt = stmt.where(ModelCredential.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                model_credential_model = pg_result.scalars().first()
                if model_credential_model is None:
                    raise Exception(f"Model credential with id {model_credential_id} not found")
                return ModelCredentialGetSchema(**model_credential_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get model credential", "error": str(e)})
            raise e

    async def delete(self, model_credential_id: uuid.UUID) -> bool:
        try:
            async with self.client.get_session() as session:
                stmt = select(ModelCredential)
                stmt = stmt.where(ModelCredential.id == model_credential_id)
                stmt = stmt.where(ModelCredential.org_id == self.org_id)

                pg_result = await session.execute(stmt)
                if pg_result is None:
                    raise Exception(f"Model credential with id {model_credential_id} not found")

                model_credential_model = pg_result.scalars().first()
                await session.delete(model_credential_model)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete model credential", "error": str(e)})
            raise e

    async def get_all(self, provider: str) -> list[ModelCredentialGetSchema]:
        try:
            async with self.client.get_session() as session:
                stmt = select(ModelCredential)
                stmt = stmt.where(ModelCredential.provider == provider)
                stmt = stmt.where(ModelCredential.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result = pg_result.scalars().all()
                return [ModelCredentialGetSchema(**model_credential.to_dict()) for model_credential in result]
        except Exception as e:
            logger.error({"message": "Failed to get all model credentials", "error": str(e)})
            raise e
