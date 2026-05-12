from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from ..databases.redis.client import GRedisClient
from app.utils.logger import logger
from app.constants import redis
from typing import List, Dict
from numpy import array
import uuid
import json


class GRedisSparseEmbeddingClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.client = GRedisClient().get_client()

    def _build_temp_key(self, document_id: uuid.UUID) -> str:
        prefix_key = redis.GRedisKeys.SPARSE_EMBEDDINGS_TEMP_KEY
        return f"{prefix_key}:{self.org_id}:{self.project_id}:{document_id}"

    async def add_sparse_embedding_temporary(
        self,
        document_id: uuid.UUID,
        chunk_number: int,
        sparse_embedding: SparseEmbedding,
        ttl: int = 604800,  # 7 days
    ):
        try:
            key = self._build_temp_key(document_id)
            data: dict = {
                "chunk_number": chunk_number,
                "indices": sparse_embedding.indices.tolist(),   # numpy → list
                "values": sparse_embedding.values.tolist(),     # numpy → list
            }

            result = await self.client.rpush(key, json.dumps(data))  # type: ignore

            if result:
                await self.client.expire(key, ttl)
            else:
                logger.error({"message": "Failed to add sparse embedding temporary", "result": result})
                raise Exception("Failed to add sparse embedding temporary")

            return result
        except Exception as e:
            logger.error({"message": "Failed to add sparse embedding temporary", "error": str(e)})
            return None

    async def get_all_temporary_sparse_embeddings(self, document_id: uuid.UUID) -> Dict[int, SparseEmbedding]:
        try:
            key = self._build_temp_key(document_id)

            raw_results = await self.client.lrange(key, 0, -1)  # type: ignore

            if not raw_results:
                return {}

            result: Dict[int, SparseEmbedding] = {}

            for item in raw_results:
                parsed = json.loads(item)
                chunk_number = parsed["chunk_number"]
                result[chunk_number] = SparseEmbedding(
                    indices=array(parsed["indices"]),
                    values=array(parsed["values"]),
                )

            return result
        except Exception as e:
            logger.error({"message": "Failed to get sparse embedding temporary", "error": str(e)})
            return {}
