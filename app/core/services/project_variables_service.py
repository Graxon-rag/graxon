from ..schemas.project_variables_schema import ProjectVariableBase
from ..repos.project_variables_repo import ProjectVariableRepo
from app.utils.logger import logger
import uuid


class ProjectVariableService:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self._repo = ProjectVariableRepo(org_id, project_id)

    async def get_by_project(self) -> ProjectVariableBase | None:
        try:
            return await self._repo.get_by_project()
        except Exception as e:
            logger.error({"message": "Failed to get project variables", "error": str(e)})
            raise e
