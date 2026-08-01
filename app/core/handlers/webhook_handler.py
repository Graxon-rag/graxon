from ..schemas.webhook_schema import WebhookCreateSchema, WebhookGetSchema
from ..services.webhook_service import WebhookService
from app.utils.logger import logger
import uuid


class WebhookHandler:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.service = WebhookService(org_id=org_id, project_id=project_id)

    async def create(self, w: WebhookCreateSchema) -> WebhookGetSchema:
        try:
            return await self.service.create(w)
        except Exception as e:
            logger.error({"message": "Failed to create webhook", "error": str(e)})
            raise e

    async def get(self, webhook_id: uuid.UUID) -> WebhookGetSchema | None:
        try:
            return await self.service.get(webhook_id)
        except Exception as e:
            logger.error({"message": "Failed to get webhook", "error": str(e)})
            raise e

    async def list(self) -> list[WebhookGetSchema]:
        try:
            return await self.service.list()
        except Exception as e:
            logger.error({"message": "Failed to list webhook", "error": str(e)})
            raise e

    async def delete(self, webhook_id: uuid.UUID) -> bool:
        try:
            return await self.service.delete(webhook_id)
        except Exception as e:
            logger.error({"message": "Failed to delete webhook", "error": str(e)})
            raise e
