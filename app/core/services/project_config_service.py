from ..schemas.project_config_schema import ProjectConfigCreateSchema, ProjectConfigGetSchema, ProjectConfigUpdateSchema, ProjectConfigDetailGetSchema
from ..repos.project_config_repo import ProjectConfigRepo
from ..helpers.project_helper import ProjectConfigHelper
from app.utils.logger import logger
import uuid


class ProjectConfigService:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self._repo = ProjectConfigRepo(org_id, project_id)

    async def create(self, p: ProjectConfigCreateSchema) -> ProjectConfigGetSchema:
        try:
            return await self._repo.create(p)
        except Exception as e:
            logger.error({"message": "Failed to create project config", "error": str(e)})
            raise e

    async def get_by_project(self) -> ProjectConfigGetSchema | None:
        try:
            return await self._repo.get_by_project()
        except Exception as e:
            logger.error({"message": "Failed to get project config", "error": str(e)})
            raise e

    async def get_with_details_by_project(self, is_external_call: bool = True) -> ProjectConfigDetailGetSchema | None:
        try:
            pc = await self._repo.get_by_project()
            if pc is None:
                return None
            pc_helper = ProjectConfigHelper(self._repo.org_id, self._repo.project_id)
            return await pc_helper.get_project_config_detail(pc, is_external_call)
        except Exception as e:
            logger.error({"message": "Failed to get project config", "error": str(e)})
            raise e

    async def get(self, config_id: uuid.UUID) -> ProjectConfigGetSchema | None:
        try:
            return await self._repo.get(config_id)
        except Exception as e:
            logger.error({"message": "Failed to get project config", "error": str(e)})
            raise e

    async def update(self, config_id: uuid.UUID, u: ProjectConfigUpdateSchema) -> ProjectConfigGetSchema:
        try:
            return await self._repo.update(config_id, u)
        except Exception as e:
            logger.error({"message": "Failed to update project config", "error": str(e)})
            raise e

    async def delete(self, config_id: uuid.UUID) -> bool:
        try:
            return await self._repo.delete(config_id)
        except Exception as e:
            logger.error({"message": "Failed to delete project config", "error": str(e)})
            raise e
