from ..schemas.project_schema import ProjectCreateSchema, ProjectGetSchema
from ..services.project_service import ProjectService
from app.utils.logger import logger
import uuid


class ProjectHandler:
    def __init__(self, org_id: str):
        self._service = ProjectService(org_id)

    async def create(self, data: ProjectCreateSchema) -> ProjectGetSchema:
        try:
            return await self._service.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create project", "error": str(e)})
            raise e

    async def get_all(self) -> list[ProjectGetSchema]:
        try:
            return await self._service.get_all()
        except Exception as e:
            logger.error({"message": "Failed to get projects", "error": str(e)})
            raise e

    async def get(self, project_id: uuid.UUID) -> ProjectGetSchema | None:
        try:
            return await self._service.get(project_id)
        except Exception as e:
            logger.error({"message": "Failed to get project", "error": str(e)})
            raise e

    async def delete(self, project_id: uuid.UUID) -> bool:
        try:
            return await self._service.delete(project_id)
        except Exception as e:
            logger.error({"message": "Failed to delete project", "error": str(e)})
            raise e
