from ..databases.qdrant.client import GQdrantClient
from app.utils.logger import logger
from qdrant_client.models import Filter, FieldCondition, MatchValue
import uuid


class QDrantCleaner:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.qdrant_client = GQdrantClient.get_client()

    async def delete(self, model_key: str, document_id: uuid.UUID):
        try:
            coll, _ = GQdrantClient._get_collection_vector_name(model_key)
            client = self.qdrant_client
            delete_filter = Filter(
                must=[
                    FieldCondition(key="org_id", match=MatchValue(value=self.org_id)),
                    FieldCondition(key="project_id", match=MatchValue(value=str(self.project_id))),
                    FieldCondition(key="document_id", match=MatchValue(value=str(document_id))),
                ]
            )

            await client.delete(
                collection_name=coll,
                points_selector=delete_filter
            )

        except Exception as e:
            logger.error({"message": "Failed to delete document", "error": str(e)})
            raise e
