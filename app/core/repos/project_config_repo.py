from ..schemas.project_config_schema import ProjectConfigGetSchema, ProjectConfigCreateSchema, ProjectConfigUpdateSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import ProjectConfig
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class ProjectConfigRepo:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self._db = GPostgresqlClient()
        self.org_id = org_id
        self.project_id = project_id

    async def create(self, p: ProjectConfigCreateSchema, session=None) -> ProjectConfigGetSchema:
        try:
            # If a session is passed in, use it. Otherwise, create a new one.
            if session:
                return await self._execute_create(session, p)
            else:
                async with self._db.get_session() as new_session:
                    return await self._execute_create(new_session, p)
        except Exception as e:
            logger.error({"message": "Failed to create project config", "error": str(e)})
            raise e

    async def _execute_create(self, session, p: ProjectConfigCreateSchema):
        config = ProjectConfig(project_id=self.project_id, **p.model_dump())
        session.add(config)

        # Flush instead of commit so the parent transaction still controls the final commit
        await session.flush() 
        return ProjectConfigGetSchema(**config.to_dict())

    async def get_by_project(self) -> ProjectConfigGetSchema | None:
        try:
            async with self._db.get_session() as session:
                config = await session.scalar(select(ProjectConfig).where(ProjectConfig.project_id == self.project_id))
                if config is None:
                    raise Exception(f"Project config with project id {self.project_id} not found")
                return ProjectConfigGetSchema(**config.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get project config", "error": str(e)})
            raise e

    async def get(self, config_id: uuid.UUID) -> ProjectConfigGetSchema | None:
        try:
            async with self._db.get_session() as session:
                config = await session.scalar(select(ProjectConfig).where(ProjectConfig.id == config_id))
                if config is None:
                    raise Exception(f"Project config with id {config_id} not found")
                return ProjectConfigGetSchema(**config.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get project config", "error": str(e)})
            raise e

    async def update(self, config_id: uuid.UUID, u: ProjectConfigUpdateSchema) -> ProjectConfigGetSchema:
        try:
            async with self._db.get_session() as session:
                config = await session.scalar(
                    select(ProjectConfig).where(
                        ProjectConfig.id == config_id
                    )
                )

                if config is None:
                    raise Exception(
                        f"Project config with id {config_id} not found"
                    )

                update_data = u.model_dump(exclude_unset=True)

                for field, value in update_data.items():
                    setattr(config, field, value)

                await session.commit()
                await session.refresh(config)

            return ProjectConfigGetSchema.model_validate(config)
        except Exception as e:
            logger.error({"message": "Failed to update project config", "error": str(e)})
            raise e

    async def delete(self, config_id: uuid.UUID) -> bool:
        try:
            async with self._db.get_session() as session:
                config = await session.scalar(select(ProjectConfig).where(ProjectConfig.id == config_id))
                if config is None:
                    raise Exception(f"Project config with id {config_id} not found")
                await session.delete(config)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete project config", "error": str(e)})
            raise e
