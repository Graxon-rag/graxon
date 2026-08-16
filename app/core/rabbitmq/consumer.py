from ..schemas.document_schema import DocumentStatusMQSchema
from ..helpers.webhook_helper import WebhookConsumerHelper
from ..services.document_service import DocumentService
from ..schemas.webhook_schema import WebhookSendParams
from app.constants.document import DocumentStatus
from aio_pika.abc import AbstractIncomingMessage
from ..helpers.rmq import RMQProcessorHelper
from ..schemas import processor_schema as ps
from app.constants.rabbitmq import GQueues
from .producer import GMQDocumentProducer
from .client import GRabbitMQClient
from app.utils.logger import logger


class GMQWebhookConsumer:
    async def consume_webhook_queue(self):
        try:
            logger.info(f"[✓] Started consuming from queue: {GQueues.WEBHOOK_QUEUE}")

            channel = await GRabbitMQClient.create_channel()

            await channel.set_qos(prefetch_count=1)  # Set the prefetch count to 1 so we only get one message at a time from the queue and process it

            queue = await channel.get_queue(GQueues.WEBHOOK_QUEUE)

            await queue.consume(self._on_webhook_message, no_ack=False)

            logger.info(f"[✓] Consuming from queue: {GQueues.WEBHOOK_QUEUE}")
        except Exception as e:
            logger.error({"message": "Failed to consume message", "error": str(e)})
            raise e

    async def _on_webhook_message(self, message: AbstractIncomingMessage):
        async with message.process(requeue=False, ignore_processed=True):
            try:
                retry_count = self._get_retry_count(message)
                if retry_count > 3:
                    logger.error({"message": "Max retries exceeded, skipping message for sending webhook event", "retry_count": retry_count})
                    await message.ack()  # ack to drop it permanently, not reject/nack
                    return

                body = message.body.decode()
                webhook_data = WebhookSendParams.model_validate_json(body)
                await WebhookConsumerHelper().handle_webhook_send(webhook_data)

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
                retry_count = self._get_retry_count(message)
                if retry_count > 3:
                    logger.error({"message": "Max retries exceeded, skipping message for updating document status", "retry_count": retry_count})
                    await message.ack()  # ack to drop it permanently, not reject/nack
                    return

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
        print("\n**************** $$$$ ******************")
        logger.info({"message": "Processing document", "file_type": file_type, "common_params": cp.model_dump(mode="json", exclude_none=True)})

        # IMPORTANT: route on which params field is actually populated on
        # THIS message, not on file_type alone. file_type reflects the
        # *original* document and stays fixed across the whole pipeline —
        # e.g. an image (or a PDF/DOC/PPT with is_ocr_needed=True) keeps
        # file_type=IMAGE/PDF/DOC/PPT even once it's mid-OCR and emitting
        # md_params or ocr_params messages instead of its "native" params.
        # These two checks MUST come before the file_type match below,
        # otherwise those messages get routed into the wrong case and hit
        # a "params is None" error even though the params object exists,
        # just under a different field.
        if data.md_params is not None:
            await RMQProcessorHelper.handle_markdown(cp, data.md_params)
            print("\n****************** @@@@@ ****************")
            return

        if data.ocr_params is not None:
            await RMQProcessorHelper.handle_ocr(cp, data.ocr_params)
            print("\n****************** @@@@@ ****************")
            return

        match file_type:
            # Audio
            case ps.FileType.AUDIO:
                if data.audio_params is None:
                    raise ValueError("Audio params is None")
                await RMQProcessorHelper.handle_audio(cp, data.audio_params)

            # Image
            case ps.FileType.IMAGE:
                # Should have been handled by the ocr_params check above.
                raise ValueError("Image params is None")

            # Video
            case ps.FileType.VIDEO:
                if data.video_params is None:
                    raise ValueError("Video params is None")
                await RMQProcessorHelper.handle_video(cp, data.video_params)

            # Text
            case ps.FileType.CODE:
                if data.code_params is None:
                    raise ValueError("Code params is None")
                await RMQProcessorHelper.handle_code(cp, data.code_params)
            case ps.FileType.TEXT:
                if data.txt_params is None:
                    raise ValueError("Text params is None")
                await RMQProcessorHelper.handle_txt(cp, data.txt_params)
            case ps.FileType.JSON:
                if data.json_params is None:
                    raise ValueError("JSON params is None")
                await RMQProcessorHelper.handle_json(cp, data.json_params)
            case ps.FileType.MARKDOWN:
                if data.md_params is None:
                    raise ValueError("Markdown params is None")
                await RMQProcessorHelper.handle_markdown(cp, data.md_params)
            case ps.FileType.PDF:
                if data.pdf_params is not None:
                    await RMQProcessorHelper.handle_pdf(cp, data.pdf_params)
                else:
                    # is_ocr_needed=True case should have been caught by the
                    # ocr_params/md_params checks above; if we're here, both
                    # were missing too.
                    raise ValueError("PDF params is None")
            case ps.FileType.DOC:
                if data.docx_params is not None:
                    await RMQProcessorHelper.handle_docx(cp, data.docx_params)
                else:
                    # is_ocr_needed=True case should have been caught by the
                    # ocr_params/md_params checks above; if we're here, both
                    # were missing too.
                    raise ValueError("Docx params is None")
            case ps.FileType.PPT:
                if data.ppt_params is not None:
                    await RMQProcessorHelper.handle_ppt(cp, data.ppt_params)
                else:
                    # is_ocr_needed=True case should have been caught by the
                    # ocr_params/md_params checks above; if we're here, both
                    # were missing too.
                    raise ValueError("PPT params is None")
            case ps.FileType.EXCEL:
                if data.excel_params is None:
                    raise ValueError("Excel params is None")
                await RMQProcessorHelper.handle_excel(cp, data.excel_params)
            case ps.FileType.HTML:
                if data.html_params is None:
                    raise ValueError("HTML params is None")
                await RMQProcessorHelper.handle_html(cp, data.html_params)
            case ps.FileType.CSV:
                if data.csv_params is None:
                    raise ValueError("CSV params is None")
                await RMQProcessorHelper.handle_csv(cp, data.csv_params)
            case ps.FileType.XML:
                if data.xml_params is None:
                    raise ValueError("XML params is None")
                await RMQProcessorHelper.handle_xml(cp, data.xml_params)
            case ps.FileType.YAML:
                if data.yaml_params is None:
                    raise ValueError("YAML params is None")
                await RMQProcessorHelper.handle_yaml(cp, data.yaml_params)
            case _:
                raise ValueError(f"Unsupported file type: {file_type.value.lower()}")
        print("\n****************** @@@@@ ****************")
