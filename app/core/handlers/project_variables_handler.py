from ..services.project_variables_service import ProjectVariableService
from ..schemas.project_variables_schema import ProjectVariableBase
from app.utils.logger import logger
import uuid


class ProjectVariableHandler:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self._service = ProjectVariableService(org_id, project_id)

    async def get_by_project(self) -> ProjectVariableBase | None:
        try:
            return await self._service.get_by_project()
        except Exception as e:
            logger.error({"message": "Failed to get project variables", "error": str(e)})
            raise e
