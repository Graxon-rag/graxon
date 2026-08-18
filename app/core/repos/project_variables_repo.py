from ..schemas.project_variables_schema import ProjectVariableBase, ProjectVariableCreateSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import ProjectVariable
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class ProjectVariableRepo:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self._db = GPostgresqlClient()
        self.org_id = org_id
        self.project_id = project_id

    async def create(self, p: ProjectVariableCreateSchema, session: AsyncSession):
        try:
            project_variable = ProjectVariable(project_id=self.project_id, **p.model_dump())
            session.add(project_variable)
            await session.flush()
            return project_variable
        except Exception as e:
            logger.error(e)
            return

    async def get_by_project(self) -> ProjectVariableBase | None:
        try:
            async with self._db.get_session() as session:
                project_variable = await session.scalar(
                    select(ProjectVariable).where(ProjectVariable.project_id == self.project_id)
                )
                if project_variable is None:
                    raise Exception(f"Project variable with project id {self.project_id} not found")
                return ProjectVariableBase(**project_variable.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get project variable", "error": str(e)})
            raise e
