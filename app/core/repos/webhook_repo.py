from ..schemas.webhook_schema import WebhookCreateSchema, WebhookGetSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import Webhook
from .project_repo import ProjectRepo
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class WebhookRepo:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.db = GPostgresqlClient()
        self._project_repo = ProjectRepo(org_id=self.org_id)

    async def _get_project(self):
        try:
            return await self._project_repo.get(self.project_id)
        except Exception as e:
            logger.error({"message": "Failed to get project", "error": str(e)})
            raise e

    async def create(self, w: WebhookCreateSchema) -> WebhookGetSchema:
        try:
            project = await self._get_project()
            if project is None:
                raise Exception(f"Project with id {self.project_id} not found")

            async with self.db.get_session() as session:
                webhook = Webhook(
                    org_id=self.org_id,
                    project_id=self.project_id,
                    name=w.name,
                    url=w.url,
                    token=w.token
                )
                session.add(webhook)
                await session.commit()
                get_result = await self.get(webhook.id)
                if get_result is None:
                    raise Exception(f"Webhook with id {webhook.id} not found")
                return get_result
        except Exception as e:
            logger.error({"message": "Failed to create webhook", "error": str(e)})
            raise e

    async def get(self, id: uuid.UUID) -> WebhookGetSchema | None:
        try:
            project = await self._get_project()
            if project is None:
                raise Exception(f"Project with id {self.project_id} not found")

            async with self.db.get_session() as session:
                stmt = select(Webhook)
                stmt = stmt.where(Webhook.id == id)
                stmt = stmt.where(Webhook.org_id == self.org_id)
                stmt = stmt.where(Webhook.project_id == self.project_id)
                pg_result = await session.execute(stmt)
                webhook = pg_result.scalars().first()
                if webhook is None:
                    raise Exception(f"Webhook with id {id} not found")
                return WebhookGetSchema(**webhook.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get webhook", "error": str(e)})
            raise e

    async def list(self) -> list[WebhookGetSchema]:
        try:
            project = await self._get_project()
            if project is None:
                raise Exception(f"Project with id {self.project_id} not found")

            async with self.db.get_session() as session:
                stmt = select(Webhook)
                stmt = stmt.where(Webhook.org_id == self.org_id)
                stmt = stmt.where(Webhook.project_id == self.project_id)
                pg_result = await session.execute(stmt)
                result = pg_result.scalars().all()
                return [WebhookGetSchema(**webhook.to_dict()) for webhook in result]
        except Exception as e:
            logger.error({"message": "Failed to list webhook", "error": str(e)})
            raise e

    async def delete(self, id: uuid.UUID) -> bool:
        try:
            project = await self._get_project()
            if project is None:
                raise Exception(f"Project with id {self.project_id} not found")

            async with self.db.get_session() as session:
                stmt = select(Webhook)
                stmt = stmt.where(Webhook.id == id)
                stmt = stmt.where(Webhook.org_id == self.org_id)
                stmt = stmt.where(Webhook.project_id == self.project_id)
                pg_result = await session.execute(stmt)
                webhook = pg_result.scalars().first()
                if webhook is None:
                    raise Exception(f"Webhook with id {id} not found")
                await session.delete(webhook)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete webhook", "error": str(e)})
            raise e
