from .client import GRabbitMQClient
from app.utils.logger import logger
from app.constants.rabbitmq import GQueues, GRoutingKeys, GExchanges
from ..schemas.document_schema import DocumentGetSchema
import aio_pika


class GMQDocumentProducer:

    @staticmethod
    async def publish(document: DocumentGetSchema):
        try:
            ch = await GRabbitMQClient.create_channel()
            exchange = await ch.get_exchange(GExchanges.DOCUMENT_PROCESSING_EXCHANGE)
            routing_key = GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY

            doc_str = document.model_dump_json().encode("utf-8")
            message = aio_pika.Message(
                body=doc_str,
            )
            logger.info({"message": "Sending message to exchange", "routing_key": routing_key, "document_id": document.id, "data": document.model_dump()})

            await exchange.publish(message=message, routing_key=routing_key)

            logger.info({"message": "Message sent to exchange", "routing_key": routing_key, "document_id": document.id})
        except Exception as e:
            logger.error({"message": "Failed to send message", "error": str(e)})
            raise e
