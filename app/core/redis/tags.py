from ..databases.redis.client import GRedisClient
from app.utils.logger import logger
from app.constants import redis
from typing import Dict, Any
import uuid


class GRedisTagsClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.client = GRedisClient().get_client()

    #  Adding tags for temporary for checkpoint into array
    async def add_tag_temporary(self, document_id: uuid.UUID, chunk_number: int, data: Dict[str, Any], ttl: int = 604800):  # 1 week
        try:
            str_project_id = str(self.project_id)
            str_document_id = str(document_id)
            prefix_key = f"{redis.GRedisKeys.TAG_TEMP_KEY}"
            key = f"{prefix_key}:{self.org_id}:{str_project_id}:{str_document_id}"

            data_object: Dict[str, Any] = {
                "chunk_number": chunk_number,
                "data": data
            }

            # Recommendation: Use json.dumps(data_object) instead of str() for better compatibility
            data_obj_str = str(data_object)

            # Push the data to the list
            result = self.client.rpush(key, data_obj_str)

            if result:
                # Set the TTL (expire) on the key
                # This ensures the entire list is deleted after the ttl seconds
                self.client.expire(key, ttl)
            else:
                logger.error({"message": "Failed to add tag temporary", "result": result})
                raise Exception("Failed to add tag temporary")

            return result
        except Exception as e:
            logger.error({"message": "Failed to add tag temporary", "error": str(e)})
            raise e

    async def get_tag_temporary(self, document_id: uuid.UUID):
        try:
            str_project_id = str(self.project_id)
            str_document_id = str(document_id)
            prefix_key = f"{redis.GRedisKeys.TAG_TEMP_KEY}"
            key = f"{prefix_key}:{self.org_id}:{str_project_id}:{str_document_id}"

            result = self.client.lrange(key, 0, -1)

            if result is None:
                logger.error({"message": "Failed to get tag temporary", "result": result})
                raise Exception("Failed to get tag temporary")

            return result
        except Exception as e:
            logger.error({"message": "Failed to get tag temporary", "error": str(e)})
            raise e
