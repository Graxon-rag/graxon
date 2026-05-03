from .client import GRabbitMQClient
from app.utils.logger import logger


class GProcessDocumentProducer:
    def __init__(self, org_id: str, project_id: str):
        self.org_id = org_id
        self.project_id = project_id
        self._client = GRabbitMQClient()

    async def send(self,):
        try:
            ch = await self._client.get_channel()
            # ch.declare_exchange()
        except Exception as e:
            logger.error({"message": "Failed to send message", "error": str(e)})
            raise e
