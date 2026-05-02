from ..repos.org_repo import OrgRepo
from ..schemas.org_schema import OrgCreateSchema, OrgGetSchema
from app.utils.logger import logger


class OrgService:
    def __init__(self):
        self.repo = OrgRepo()

    async def create(self, data: OrgCreateSchema) -> OrgGetSchema:
        try:
            return await self.repo.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create organization", "error": str(e)})
            raise e

    async def get(self, org_id: str) -> OrgGetSchema:
        try:
            return await self.repo.get(org_id)
        except Exception as e:
            logger.error({"message": "Failed to get organization", "error": str(e)})
            raise e

    async def get_all(self) -> list[OrgGetSchema]:
        try:
            return await self.repo.get_all()
        except Exception as e:
            logger.error({"message": "Failed to get organizations", "error": str(e)})
            raise e

    async def delete(self, org_id: str) -> None:
        try:
            return await self.repo.delete(org_id)
        except Exception as e:
            logger.error({"message": "Failed to delete organization", "error": str(e)})
            raise e
