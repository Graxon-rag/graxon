from ..schemas.project_schema import ProjectCreateSchema, ProjectGetSchema, ProjectDetailSchema
from ..repos.project_repo import ProjectRepo
from app.utils.logger import logger
import uuid


class ProjectService:
    def __init__(self, org_id: str):
        self._repo = ProjectRepo(org_id)

    async def create(self, data: ProjectCreateSchema) -> ProjectGetSchema:
        try:
            project = await self._repo.create(data)
            return project
        except Exception as e:
            logger.error({"message": "Failed to create project", "error": str(e)})
            raise e

    async def get_all(self) -> list[ProjectGetSchema]:
        try:
            return await self._repo.get_all()
        except Exception as e:
            logger.error({"message": "Failed to get projects", "error": str(e)})
            raise e

    async def get(self, project_id: uuid.UUID) -> ProjectGetSchema | None:
        try:
            return await self._repo.get(project_id)
        except Exception as e:
            logger.error({"message": "Failed to get project", "error": str(e)})
            raise e

    async def get_project_details(self, project_id: uuid.UUID) -> ProjectDetailSchema | None:
        try:
            return await self._repo.get_project_details(project_id)
        except Exception as e:
            logger.error({"message": "Failed to get project details", "error": str(e)})
            raise e

    async def delete(self, project_id: uuid.UUID) -> bool:
        try:
            return await self._repo.delete(project_id)
        except Exception as e:
            logger.error({"message": "Failed to delete project", "error": str(e)})
            raise e
