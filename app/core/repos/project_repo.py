from ..schemas.project_schema import ProjectCreateSchema, ProjectGetSchema, ProjectDetailSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import Project
from ..helpers.project_helper import ProjectHelper
from ..libs.id import IDLibs
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class ProjectRepo:
    def __init__(self, org_id: str):
        self._db = GPostgresqlClient()
        self.org_id = org_id

    async def create(self, data: ProjectCreateSchema) -> ProjectGetSchema:
        try:
            async with self._db.get_session() as session:
                readable_id = IDLibs.generate_project_id(data.name)

                stmt = select(Project).where(Project.readable_id == readable_id)
                pg_result = await session.execute(stmt)
                existing = pg_result.scalar_one_or_none()

                if existing is not None:
                    raise Exception(
                        f"Project with readable_id {readable_id} already exists, please change the name of the project"
                    )

                project = Project(
                    readable_id=readable_id,
                    name=data.name,
                    org_id=self.org_id,
                    description=data.description,
                    llm_model_id=data.llm_model_id,
                    embedding_model_id=data.embedding_model_id,
                    sparse_text_model_id=data.sparse_text_model_id,
                    reranker_model_id=data.reranker_model_id,
                    llm_model_credential_id=data.llm_model_credential_id,
                    embedding_model_credential_id=data.embedding_model_credential_id,
                )
                session.add(project)
                await session.commit()
                return ProjectGetSchema(**project.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to create project", "error": str(e)})
            raise e

    async def get(self, project_id: uuid.UUID) -> ProjectGetSchema | None:
        try:
            async with self._db.get_session() as session:
                stmt = select(Project)
                stmt = stmt.where(Project.id == project_id)
                stmt = stmt.where(Project.org_id == self.org_id)

                project = await session.scalar(stmt)
                if project is None:
                    raise Exception(f"Project with id {project_id} not found")
                return ProjectGetSchema(**project.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get project", "error": str(e)})
            raise e

    async def get_project_details(self, project_id: uuid.UUID) -> ProjectDetailSchema | None:
        try:
            project = await self.get(project_id)
            if project is None:
                raise Exception(f"Project with id {project_id} not found")
            project_details = await ProjectHelper(self.org_id).get_project_details(project)
            return project_details
        except Exception as e:
            logger.error({"message": "Failed to get project details", "error": str(e)})
            raise e

    async def get_all(self) -> list[ProjectGetSchema]:
        try:
            async with self._db.get_session() as session:
                projects = await session.scalars(select(Project).where(Project.org_id == self.org_id))
                return [ProjectGetSchema(**project.to_dict()) for project in projects]
        except Exception as e:
            logger.error({"message": "Failed to get projects", "error": str(e)})
            raise e

    async def delete(self, project_id: uuid.UUID) -> bool:
        try:
            async with self._db.get_session() as session:
                project = await session.scalar(select(Project).where(Project.id == project_id))
                if project is None:
                    raise Exception(f"Project with id {project_id} not found")
                await session.delete(project)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete project", "error": str(e)})
            raise e
