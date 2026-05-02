from ..services.org_service import OrgService
from ..schemas.org_schema import OrgCreateSchema, OrgGetSchema
from app.utils.logger import logger


class OrgHandler:
    def __init__(self):
        self.service = OrgService()

    async def create(self, data: OrgCreateSchema) -> OrgGetSchema:
        try:
            return await self.service.create(data)
        except Exception as e:
            logger.error({"message": "Failed to create organization", "error": str(e)})
            raise e

    async def get(self, org_id: str) -> OrgGetSchema:
        try:
            return await self.service.get(org_id)
        except Exception as e:
            logger.error({"message": "Failed to get organization", "error": str(e)})
            raise e

    async def get_all(self) -> list[OrgGetSchema]:
        try:
            return await self.service.get_all()
        except Exception as e:
            logger.error({"message": "Failed to get organizations", "error": str(e)})
            raise e

    async def delete(self, org_id: str) -> bool:
        try:
            return await self.service.delete(org_id)
        except Exception as e:
            logger.error({"message": "Failed to delete organization", "error": str(e)})
            raise e
