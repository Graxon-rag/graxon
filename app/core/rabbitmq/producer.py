from .client import GRabbitMQClient
from app.utils.logger import logger
from app.constants.rabbitmq import GQueues, GRoutingKeys, GExchanges
from ..schemas.document_schema import DocumentGetSchema, DocumentStatusMQSchema
import aio_pika


class GMQDocumentProducer:

    @staticmethod
    async def publish_to_processing_exchange(document: DocumentGetSchema):
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

    @staticmethod
    async def publish_to_status_exchange(data: DocumentStatusMQSchema):
        try:
            ch = await GRabbitMQClient.create_channel()
            exchange = await ch.get_exchange(GExchanges.DOCUMENT_STATUS_EXCHANGE)
            routing_key = GRoutingKeys.DOCUMENT_STATUS_ROUTING_KEY

            doc_str = data.model_dump_json().encode("utf-8")
            message = aio_pika.Message(
                body=doc_str,
            )
            logger.info({"message": "Sending message to exchange", "routing_key": routing_key, "document_id": data.id, "data": data.model_dump()})

            await exchange.publish(message=message, routing_key=routing_key)

            logger.info({"message": "Message sent to exchange", "routing_key": routing_key, "document_id": data.id})
        except Exception as e:
            logger.error({"message": "Failed to send message", "error": str(e)})
            raise e
