from ..databases.redis.client import GRedisClient
from app.utils.logger import logger
from app.constants import redis
from typing import Dict, List
import uuid
import json


class GRedisEmbeddingsClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.client = GRedisClient().get_client()

    def _build_temp_key(self, document_id: uuid.UUID) -> str:
        prefix_key = redis.GRedisKeys.EMBEDDINGS_TEMP_KEY
        return f"{prefix_key}:{self.org_id}:{self.project_id}:{document_id}"

    async def add_embedding_temporary(
        self,
        document_id: uuid.UUID,
        chunk_number: int,
        embedding: list[float],
        ttl: int = 604800,  # 7 days
    ):
        try:
            key = self._build_temp_key(document_id)
            data: dict = {
                "chunk_number": chunk_number,
                "embedding": embedding,
            }

            result = await self.client.rpush(key, json.dumps(data))  # type: ignore

            if result:
                await self.client.expire(key, ttl)
            else:
                logger.error({"message": "Failed to add tag temporary", "result": result})
                raise Exception("Failed to add tag temporary")

            return result
        except Exception as e:
            logger.error({"message": "Failed to add embedding temporary", "error": str(e)})
            return None

    async def get_all_temporary_embeddings(self, document_id: uuid.UUID) -> Dict[int, List[float]]:
        try:
            key = self._build_temp_key(document_id)
            raw_results = await self.client.lrange(key, 0, -1)  # type: ignore

            if not raw_results:
                return {}

            result: Dict[int, List[float]] = {}
            for item in raw_results:
                parsed = json.loads(item)
                chunk_number = parsed["chunk_number"]
                result[chunk_number] = parsed["embedding"]

            return result
        except Exception as e:
            logger.error({"message": "Failed to get embedding temporary", "error": str(e)})
            return {}
