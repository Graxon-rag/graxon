from .databases.postgresql.client import GPostgresqlClient
from .schemas.org_schema import OrgCreateSchema
from .repos.org_repo import OrgRepo
from app.utils.logger import logger
from .neo4j.org import GN4jOrg
from sqlalchemy import text


class SeedDefaultData:
    def __init__(self):
        pass

    async def seed(self):
        try:
            logger.info("Seeding default data...")
            await self._ensure_seed_tracker_exists()
            is_first_time = await self._is_first_time_seed()
            if not is_first_time:
                logger.info("Data already seeded. Skipping...")
                return
            await self._pg()
            await self._neo4j()
            await self._mark_as_seeded()
            logger.info("Default data seeded successfully.")
        except Exception as e:
            logger.error({"message": "Failed to seed data", "error": str(e)})
            raise e

    async def _ensure_seed_tracker_exists(self):
        async with GPostgresqlClient.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS seed_tracker (
                    id SERIAL PRIMARY KEY,
                    seeded BOOLEAN NOT NULL DEFAULT FALSE,
                    seeded_at TIMESTAMP DEFAULT NOW()
                )
            """))
            await session.commit()

    async def _is_first_time_seed(self) -> bool:
        try:
            async with GPostgresqlClient.get_session() as session:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM seed_tracker WHERE seeded = TRUE")
                )
                count = result.scalar()
                return count == 0
        except Exception:
            return True

    async def _mark_as_seeded(self):
        async with GPostgresqlClient.get_session() as session:
            await session.execute(
                text("INSERT INTO seed_tracker (seeded) VALUES (TRUE)")
            )
            await session.commit()

    async def _neo4j(self):
        try:
            org = GN4jOrg()
            await org.create(org_id="dev", name="Development", description="Default Organization")
        except Exception as e:
            logger.error({"message": "Failed to seed neo4j", "error": str(e)})
            raise e

    async def _pg(self):
        try:
            await OrgRepo().create(OrgCreateSchema(name="dev", description="Default Organization"))
            logger.info("PostgreSQL seed data inserted successfully.")

        except Exception as e:
            logger.error({"message": "Failed to seed postgresql", "error": str(e)})
            raise e
