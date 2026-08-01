from ..schemas.webhook_schema import WebhookCreateSchema, WebhookGetSchema
from ..repos.webhook_repo import WebhookRepo
from app.utils.logger import logger
import uuid


class WebhookService:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.repo = WebhookRepo(org_id=org_id, project_id=project_id)

    async def create(self, w: WebhookCreateSchema) -> WebhookGetSchema:
        try:
            return await self.repo.create(w)
        except Exception as e:
            logger.error({"message": "Failed to create webhook", "error": str(e)})
            raise e

    async def get(self, webhook_id: uuid.UUID) -> WebhookGetSchema | None:
        try:
            return await self.repo.get(webhook_id)
        except Exception as e:
            logger.error({"message": "Failed to get webhook", "error": str(e)})
            raise e

    async def list(self) -> list[WebhookGetSchema]:
        try:
            return await self.repo.list()
        except Exception as e:
            logger.error({"message": "Failed to list webhook", "error": str(e)})
            raise e

    async def delete(self, webhook_id: uuid.UUID) -> bool:
        try:
            return await self.repo.delete(webhook_id)
        except Exception as e:
            logger.error({"message": "Failed to delete webhook", "error": str(e)})
            raise e
