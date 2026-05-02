from ..schemas.org_schema import OrgCreateSchema, OrgGetSchema
from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import Organization
from ..libs.org_lib import OrgLib
from app.utils.logger import logger
from sqlalchemy import select


class OrgRepo:
    def __init__(self):
        self.db = GPostgresqlClient()

    async def create(self, data: OrgCreateSchema) -> OrgGetSchema:
        try:
            async with self.db.get_session() as session:
                id = OrgLib.get_parsed_org_id(data.name)
                stmt = select(Organization).where(Organization.id == id)
                pg_result = await session.execute(stmt)
                existing = pg_result.scalar_one_or_none()

                if existing is not None:
                    raise Exception(
                        f"Organization with id {id} already exists, please change the name of the organization"
                    )

                org = Organization(
                    id=id,
                    name=data.name,
                    description=data.description
                )
                session.add(org)
                await session.commit()
                return OrgGetSchema(**org.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to create organization", "error": str(e)})
            raise e

    async def get(self, org_id: str) -> OrgGetSchema:
        try:
            async with self.db.get_session() as session:
                org = await session.scalar(select(Organization).where(Organization.id == org_id))
                if org is None:
                    raise Exception(f"Organization with id {org_id} not found")
                return OrgGetSchema(**org.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get organization", "error": str(e)})
            raise e

    async def get_all(self) -> list[OrgGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(Organization)
                pg_result = await session.execute(stmt)
                result_list = list(pg_result.scalars().all())
                return [OrgGetSchema(**org.to_dict()) for org in result_list]
        except Exception as e:
            logger.error({"message": "Failed to get organizations", "error": str(e)})
            raise e

    async def delete(self, org_id: str) -> None:
        try:
            async with self.db.get_session() as session:
                org = await session.scalar(select(Organization).where(Organization.id == org_id))
                if org is None:
                    raise Exception(f"Organization with id {org_id} not found")
                await session.delete(org)
                await session.commit()
        except Exception as e:
            logger.error({"message": "Failed to delete organization", "error": str(e)})
            raise e
