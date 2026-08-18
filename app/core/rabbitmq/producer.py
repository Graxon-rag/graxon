from ..schemas.document_schema import DocumentStatusMQSchema
from app.constants.rabbitmq import GRoutingKeys, GExchanges
from ..schemas.webhook_schema import WebhookSendParams
from ..schemas import processor_schema as ps
from .client import GRabbitMQClient
from app.utils.logger import logger
import aio_pika


class GMQDocumentProducer:

    @staticmethod
    async def publish_to_processing_exchange(data: ps.ProcessParams):
        try:
            ch = await GRabbitMQClient.create_channel()
            exchange = await ch.get_exchange(GExchanges.DOCUMENT_PROCESSING_EXCHANGE)
            routing_key = GRoutingKeys.DOCUMENT_PROCESSING_ROUTING_KEY

            data_str = data.model_dump_json().encode("utf-8")
            message = aio_pika.Message(
                body=data_str,
            )
            logger.info({"message": "Sending message to exchange", "routing_key": routing_key, "document_id": data.doc_id})

            await exchange.publish(message=message, routing_key=routing_key)

            logger.info({"message": "Message sent to exchange", "routing_key": routing_key, "document_id": data.doc_id})
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


class GMQWebhookProducer:

    @staticmethod
    async def publish_to_webhook_exchange(data: WebhookSendParams):
        try:
            ch = await GRabbitMQClient.create_channel()
            exchange = await ch.get_exchange(GExchanges.WEBHOOK_EXCHANGE)
            routing_key = GRoutingKeys.WEBHOOK_ROUTING_KEY

            data_str = data.model_dump_json().encode("utf-8")
            message = aio_pika.Message(
                body=data_str,
            )
            logger.info({"message": "Sending message to exchange", "routing_key": routing_key, "data": data.model_dump(exclude_none=True)})

            await exchange.publish(message=message, routing_key=routing_key)

            logger.info({"message": "Message sent to exchange", "routing_key": routing_key})
        except Exception as e:
            logger.error({"message": "Failed to send message", "error": str(e)})
            raise e


class GMQVectorSimilarSyncProducer:

    @staticmethod
    async def publish(data: ps.CommonParams):
        try:
            ch = await GRabbitMQClient.create_channel()
            exchange = await ch.get_exchange(GExchanges.VECTOR_SIMILAR_SYNC_EXCHANGE)
            routing_key = GRoutingKeys.VECTOR_SIMILAR_SYNC_ROUTING_KEY

            data_str = data.model_dump_json().encode("utf-8")
            message = aio_pika.Message(
                body=data_str,
            )
            logger.info({"message": "Sending message to exchange", "routing_key": routing_key, "data": data.model_dump(exclude_none=True)})

            await exchange.publish(message=message, routing_key=routing_key)

            logger.info({"message": "Message sent to exchange", "routing_key": routing_key})
        except Exception as e:
            logger.error({"message": "Failed to send message", "error": str(e)})
            raise e
