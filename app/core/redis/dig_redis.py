from ..databases.redis.client import GRedisClient
from app.utils.logger import logger
from app.constants import redis
from typing import Literal
import uuid


class DIGRedisClient:

    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id
        self.client = GRedisClient().get_client()

    def _get_dig_key(self, dig_node: str) -> str:
        return f"{redis.GRedisKeys.get_dig_node_status_prefix()}:{self.org_id}:{self.project_id}:{self.document_id}:{dig_node}"

    async def update_status(self, dig_node: str, status: Literal[
            redis.GRedisConstant.DIG_NODE_STATUS_COMPLETED,  # type: ignore
            redis.GRedisConstant.DIG_NODE_STATUS_PENDING]  # type: ignore
    ) -> bool:
        try:
            await self.client.set(self._get_dig_key(dig_node), status)
            return True
        except Exception as e:
            logger.error({"message": "Failed to update status", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            return False

    async def get_status(self, dig_node: str) -> str | None:
        try:
            status = await self.client.get(self._get_dig_key(dig_node))
            if status is None:
                return None
            logger.info({"message": "Getting status", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "dig_node": dig_node, "status": status})
            return status
        except Exception as e:
            logger.error({"message": "Failed to get status", "document_id": self.document_id, "org_id": self.org_id, "project_id": self.project_id, "error": str(e)})
            return None
