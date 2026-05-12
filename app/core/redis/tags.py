from ..databases.redis.client import GRedisClient
from app.utils.logger import logger
from typing import Dict, Any, List
from ..schemas import chunk_schema
from app.constants import redis
import uuid
import json


class GRedisTagsClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.client = GRedisClient().get_client()

    def _build_key(self, document_id: uuid.UUID) -> str:
        prefix_key = redis.GRedisKeys.TAG_TEMP_KEY
        return f"{prefix_key}:{self.org_id}:{self.project_id}:{document_id}"

    async def add_tag_temporary(
        self,
        document_id: uuid.UUID,
        chunk_number: int,
        data: chunk_schema.TagResponse,
        ttl: int = 604800,  # 7 days
    ):
        try:
            key = self._build_key(document_id)

            data_object: Dict[str, Any] = {
                "chunk_number": chunk_number,
                "data": data.model_dump()
            }

            result = await self.client.rpush(key, json.dumps(data_object))  # type: ignore

            if result:
                await self.client.expire(key, ttl)
            else:
                logger.error({"message": "Failed to add tag temporary", "result": result})
                raise Exception("Failed to add tag temporary")

            return result
        except Exception as e:
            logger.error({"message": "Failed to add tag temporary", "error": str(e)})
            raise e

    async def get_all_temporary_tags(self, document_id: uuid.UUID) -> Dict[int, List[chunk_schema.TagResponse]]:
        try:
            key = self._build_key(document_id)

            raw_results = await self.client.lrange(key, 0, -1)  # type: ignore

            if not raw_results:
                return {}

            result: Dict[int, List[chunk_schema.TagResponse]] = {}

            for item in raw_results:
                parsed = json.loads(item)
                chunk_number = parsed["chunk_number"]
                tag = chunk_schema.TagResponse(**parsed["data"])

                if chunk_number not in result:
                    result[chunk_number] = []

                result[chunk_number].append(tag)

            return result
        except Exception as e:
            logger.error({"message": "Failed to get tag temporary", "error": str(e)})
            raise e
