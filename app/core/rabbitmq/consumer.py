from .client import GRabbitMQClient
from app.utils.logger import logger
from app.constants.rabbitmq import GQueues
from ..services.document_service import DocumentService
from ..schemas.document_schema import DocumentGetSchema, DocumentStatusMQSchema
from ..schemas import processor_schema as ps
from app.constants.document import DocumentStatus
from aio_pika.abc import AbstractIncomingMessage
from .producer import GMQDocumentProducer
from ..workflow.document_workflow import DocumentWorkflow
from ..helpers.rmq import RMQHelper
import uuid


class GMQDocumentConsumer:

    async def consume_document_processing_queue(self):
        try:
            logger.info(f"[✓] Started consuming from queue: {GQueues.DOCUMENT_PROCESSING_QUEUE}")

            channel = await GRabbitMQClient.create_channel()

            await channel.set_qos(prefetch_count=1)  # Set the prefetch count to 1 so we only get one message at a time from the queue and process it

            queue = await channel.get_queue(GQueues.DOCUMENT_PROCESSING_QUEUE)

            await queue.consume(self._on_document_processing_message, no_ack=False)

            logger.info(f"[✓] Consuming from queue: {GQueues.DOCUMENT_PROCESSING_QUEUE}")
        except Exception as e:
            logger.error({"message": "Failed to consume message", "error": str(e)})
            raise e

    async def consume_document_status_queue(self):
        try:
            logger.info(f"[✓] Started consuming from queue: {GQueues.DOCUMENT_STATUS_QUEUE}")

            channel = await GRabbitMQClient.create_channel()

            await channel.set_qos(prefetch_count=1)  # Set the prefetch count to 1 so we only get one message at a time from the queue and process it

            queue = await channel.get_queue(GQueues.DOCUMENT_STATUS_QUEUE)

            await queue.consume(self._on_document_status_message, no_ack=False)

            logger.info(f"[✓] Consuming from queue: {GQueues.DOCUMENT_STATUS_QUEUE}")
        except Exception as e:
            logger.error({"message": "Failed to consume message", "error": str(e)})
            raise e

    async def _on_document_processing_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False, ignore_processed=True):
            body = message.body.decode()
            retry_count = self._get_retry_count(message)
            data = ps.ProcessParams.model_validate_json(body)
            try:
                logger.info({"message": "Received message", "retry_count": retry_count, "document": data.model_dump(mode="json", exclude_none=True)})

                if retry_count > 3:
                    logger.error({"message": "Max retries exceeded, skipping message", "retry_count": retry_count, "document": data.model_dump(mode="json", exclude_none=True)})

                    await GMQDocumentProducer.publish_to_status_exchange(DocumentStatusMQSchema(org_id=data.org_id, project_id=data.project_id, id=data.doc_id, status=DocumentStatus.FAILED))

                    await message.ack()  # ack to drop it permanently, not reject/nack
                    return

                await self._process_document(data)

                await message.ack()  # We are done with the message
            except Exception as e:
                logger.error(f"Failed to process message, sending nack → DLX: {e}")
                await message.nack(requeue=False)  # sends to DLX
                raise e

    async def _on_document_status_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False, ignore_processed=True):
            try:
                body = message.body.decode()
                doc_status = DocumentStatusMQSchema.model_validate_json(body)
                service = DocumentService(org_id=doc_status.org_id, project_id=doc_status.project_id)
                await service.change_document_status(doc_status.id, doc_status.status)

                await message.ack()  # We are done with the message
            except Exception as e:
                logger.error({"message": "Failed to update document status in MQ Consumer, skipping this again", "error": str(e)})
                await message.ack()  # We are done with the message
                raise e

    def _get_retry_count(self, message: AbstractIncomingMessage) -> int:
        try:
            x_death = message.headers.get("x-death")
            if x_death and isinstance(x_death, list) and len(x_death) > 0:
                first = x_death[0]
                if isinstance(first, dict):
                    count = first.get("count", 0)
                    if isinstance(count, (int, float)):
                        return int(count)
            return 0
        except Exception:
            return 0

    async def _process_document(self, data: ps.ProcessParams):
        file_type = data.file_type
        cp: ps.CommonParams = ps.CommonParams(
            org_id=data.org_id,
            project_id=data.project_id,
            doc_id=data.doc_id,
            file_type=file_type,
        )

        logger.info({"message": "Processing document", "file_type": file_type, "common_params": cp.model_dump(mode="json", exclude_none=True)})
        match file_type:
            # Audio
            case ps.FileType.AUDIO:
                if data.audio_params is None:
                    raise ValueError("Audio params is None")
                await RMQHelper.handle_audio(cp, data.audio_params)

            # Image
            case ps.FileType.IMAGE:
                if data.image_params is None:
                    raise ValueError("Image params is None")
                await RMQHelper.handle_image(cp, data.image_params)

            # Video
            case ps.FileType.VIDEO:
                pass

            # Text
            case ps.FileType.CODE:
                if data.code_params is None:
                    raise ValueError("Code params is None")
                await RMQHelper.handle_code(cp, data.code_params)
            case ps.FileType.TEXT:
                if data.txt_params is None:
                    raise ValueError("Text params is None")
                await RMQHelper.handle_txt(cp, data.txt_params)
            case ps.FileType.JSON:
                if data.json_params is None:
                    raise ValueError("JSON params is None")
                await RMQHelper.handle_json(cp, data.json_params)
            case ps.FileType.PDF:
                if data.pdf_params is None:
                    raise ValueError("PDF params is None")
                await RMQHelper.handle_pdf(cp, data.pdf_params)
            case ps.FileType.MARKDOWN:
                if data.md_params is None:
                    raise ValueError("Markdown params is None")
                await RMQHelper.handle_md(cp, data.md_params)
            case ps.FileType.DOC:
                if data.docx_params is None:
                    raise ValueError("Docx params is None")
                await RMQHelper.handle_docx(cp, data.docx_params)
            case ps.FileType.PPT:
                if data.ppt_params is None:
                    raise ValueError("PPT params is None")
                await RMQHelper.handle_ppt(cp, data.ppt_params)
            case ps.FileType.EXCEL:
                if data.excel_params is None:
                    raise ValueError("Excel params is None")
                await RMQHelper.handle_excel(cp, data.excel_params)
            case ps.FileType.HTML:
                if data.html_params is None:
                    raise ValueError("HTML params is None")
                await RMQHelper.handle_html(cp, data.html_params)
            case ps.FileType.CSV:
                if data.csv_params is None:
                    raise ValueError("CSV params is None")
                await RMQHelper.handle_csv(cp, data.csv_params)
            case ps.FileType.XML:
                if data.xml_params is None:
                    raise ValueError("XML params is None")
                await RMQHelper.handle_xml(cp, data.xml_params)
            case ps.FileType.YAML:
                if data.yaml_params is None:
                    raise ValueError("YAML params is None")
                await RMQHelper.handle_yaml(cp, data.yaml_params)
            case _:
                raise ValueError(f"Unsupported file type: {file_type.value.lower()}")
