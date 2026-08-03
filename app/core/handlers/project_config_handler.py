from ..schemas.project_config_schema import ProjectConfigCreateSchema, ProjectConfigGetSchema, ProjectConfigUpdateSchema
from ..services.project_config_service import ProjectConfigService
from app.utils.logger import logger
import uuid


class ProjectConfigHandler:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self._service = ProjectConfigService(org_id, project_id)

    async def create(self, p: ProjectConfigCreateSchema) -> ProjectConfigGetSchema:
        try:
            return await self._service.create(p)
        except Exception as e:
            logger.error({"message": "Failed to create project config", "error": str(e)})
            raise e

    async def get(self, config_id: uuid.UUID) -> ProjectConfigGetSchema | None:
        try:
            return await self._service.get(config_id)
        except Exception as e:
            logger.error({"message": "Failed to get project config", "error": str(e)})
            raise e

    async def update(self, config_id: uuid.UUID, u: ProjectConfigUpdateSchema) -> ProjectConfigGetSchema:
        try:
            return await self._service.update(config_id, u)
        except Exception as e:
            logger.error({"message": "Failed to update project config", "error": str(e)})
            raise e

    async def delete(self, config_id: uuid.UUID) -> bool:
        try:
            return await self._service.delete(config_id)
        except Exception as e:
            logger.error({"message": "Failed to delete project config", "error": str(e)})
            raise e
