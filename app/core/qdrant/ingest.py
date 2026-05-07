from ..databases.qdrant.client import GQdrantClient
from qdrant_client import models
from app.utils.logger import logger


class QdrantInjector:
    def __init__(self):
        self.qdrant_client = GQdrantClient.get_client()
        logger.info("Qdrant Injector initialized.")

    async def inject(self):
        try:
            client = GQdrantClient.get_client()
            # client.
        except Exception as e:
            logger.error({"message": "Failed to inject data into Qdrant", "error": str(e)})
            raise e
