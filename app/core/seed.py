from .neo4j.org import GN4jOrg
from app.utils.logger import logger


class SeedDefaultData:
    def __init__(self):
        pass

    async def seed(self):
        try:
            logger.info("Seeding default data...")
            await self._neo4j()
            logger.info("Default data seeded successfully.")
        except Exception as e:
            logger.error({
                "message": "Failed to seed data",
                "error": str(e)
            })
            raise e

    async def _neo4j(self):
        try:
            org = GN4jOrg()
            await org.create(org_id="dev", name="Development", description="Default Organization")
        except Exception as e:
            logger.error({
                "message": "Failed to seed neo4j",
                "error": str(e)
            })
            raise e
