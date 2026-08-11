from ..processor.ocr.processor_factory import OcrProcessorFactory, ProcessorEnum as ocr_enum
from ..processor.audio.processor_factory import AudioProcessorFactory
from ..processor.text.processor_factory import ProcessorFactory
from ..processor.audio.model import AudioProviderEnum
from ..rabbitmq.producer import GMQDocumentProducer
from ..schemas import processor_schema as ps
from app.utils.logger import logger


_AUDIO_PROVIDERS = {
    "assemblyai": (AudioProviderEnum.ASSEMBLYAI, {
        "speaker_labels": "speaker_labels",
        "language_detection": "language_detection",
    }),
    "deepgram": (AudioProviderEnum.DEEPGRAM, {
        "model": "deepgram_model",
        "diarize": "diarize",
        "smart_format": "smart_format",
        "detect_language": "detect_language",
    }),
    "elevenlabs": (AudioProviderEnum.ELEVENLABS, {
        "base_url": "base_url",
        "model_id": "ele_model_id",
        "tag_audio_events": "tag_audio_events",
        "diarize": "diarize",
    }),
    "gladia": (AudioProviderEnum.GLADIA, {
        "model": "gladia_model",
        "diarization": "diarization",
    }),
    "groq": (AudioProviderEnum.GROQ, {
        "model": "groq_model",
    }),
}


class RMQProducerHelper:
    @staticmethod
    async def produce_txt(cp: ps.CommonParams, txt: ps.TxtProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=txt.filename,
                        txt_params=txt
            ))

    @staticmethod
    async def produce_json(cp: ps.CommonParams, json: ps.JsonProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=json.filename,
                        json_params=json
            ))

    @staticmethod
    async def produce_xml(cp: ps.CommonParams, xml: ps.XmlProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=xml.filename,
                        xml_params=xml
            ))

    @staticmethod
    async def produce_docx(cp: ps.CommonParams, docx: ps.DocxProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=docx.filename,
                        docx_params=docx
            ))

    @staticmethod
    async def produce_pdf(cp: ps.CommonParams, pdf: ps.PdfProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=pdf.filename,
                        pdf_params=pdf
            ))

    @staticmethod
    async def produce_csv(cp: ps.CommonParams, csv: ps.CSVProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=csv.filename,
                        csv_params=csv
            ))

    @staticmethod
    async def produce_ppt(cp: ps.CommonParams, ppt: ps.PptxProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=ppt.filename,
                        ppt_params=ppt
            ))

    @staticmethod
    async def produce_excel(cp: ps.CommonParams, excel: ps.ExcelProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=excel.filename,
                        excel_params=excel
            ))

    @staticmethod
    async def produce_markdown(cp: ps.CommonParams, markdown: ps.MarkdownProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=markdown.filename,
                        md_params=markdown
            ))

    @staticmethod
    async def produce_yaml(cp: ps.CommonParams, yaml: ps.YamlProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=yaml.filename,
                        yaml_params=yaml
            ))

    @staticmethod
    async def produce_code(cp: ps.CommonParams, code: ps.CodeProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=code.filename,
                        code_params=code
            ))

    @staticmethod
    async def produce_html(cp: ps.CommonParams, html: ps.HtmlProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=html.filename,
                        html_params=html
            ))

    @staticmethod
    async def produce_audio(cp: ps.CommonParams, audio: ps.AudioProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=audio.filename,
                        audio_params=audio
            ))

    @staticmethod
    async def produce_image(cp: ps.CommonParams, image: ps.ImageProcessParams):
        await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
                        org_id=cp.org_id,
                        project_id=cp.project_id,
                        doc_id=cp.doc_id,
                        file_type=cp.file_type,
                        filename=image.filename,
                        image_params=image
            ))


class RMQProcessorHelper:
    @staticmethod
    async def handle_txt(cp: ps.CommonParams, data: ps.TxtProcessParams):
        logger.info({"message": "Processing text", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "file_chunk_number": data.file_chunk_number, "filename": data.filename, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "chunk_number": data.file_chunk_number,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "rag_chunk_size": data.rag_chunk_size,
            "rag_chunk_overlap": data.rag_chunk_overlap,
            "tail_carry_chars": data.tail_carry_chars
        }
        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="txt", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_txt(cp, data.model_copy(update={
                "file_chunk_number": data.file_chunk_number + 1,  # Increment chunk number
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last,

            }))

    @staticmethod
    async def handle_json(cp: ps.CommonParams, data: ps.JsonProcessParams):
        logger.info({"message": "Processing json", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "filename": data.filename, "start_object": data.start_object, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "start_object": data.start_object,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "objects_per_buffer": data.objects_per_buffer,
            "group_size": data.group_size,
            "max_group_size": data.max_group_size
        }
        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="json", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_json(cp, data.model_copy(update={
                "start_object": data.start_object + (data.objects_per_buffer or 500),  # add objects per buffer
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_xml(cp: ps.CommonParams, data: ps.XmlProcessParams):
        logger.info({"message": "Processing xml", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "filename": data.filename, "start_object": data.start_object, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "start_object": data.start_object,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "objects_per_buffer": data.objects_per_buffer,
            "group_size": data.group_size,
            "max_group_size": data.max_group_size
        }
        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="xml", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_xml(cp, data.model_copy(update={
                "start_object": data.start_object + (data.objects_per_buffer or 500),  # add objects per buffer
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_pdf(cp: ps.CommonParams, data: ps.PdfProcessParams):
        logger.info({"message": "Processing json", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "file_chunk_number": data.file_chunk_number, "filename": data.filename, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "chunk_number": data.file_chunk_number,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "pages_per_batch": data.pages_per_batch,
            "rag_chunk_size": data.rag_chunk_size,
            "rag_chunk_overlap": data.rag_chunk_overlap,
            "tail_carry_chars": data.tail_carry_chars
        }
        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="pdf", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process
        if not is_last:
            await RMQProducerHelper.produce_pdf(cp, data.model_copy(update={
                "file_chunk_number": data.file_chunk_number + 1,  # Increment chunk number
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_markdown(cp: ps.CommonParams, data: ps.MarkdownProcessParams):
        logger.info({
            "message": "Processing markdown",
            "common_params": cp.model_dump(mode="json", exclude_none=True),
            "data": data.model_dump(mode="json", exclude_none=True),
            "file_path": data.markdown_path,
            "file_chunk_number": data.file_chunk_number,
            "filename": data.filename,
            "rag_chunk_start_index": data.rag_chunk_start_index,
        })

        kwargs = {
            "chunk_number": data.file_chunk_number,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "tokenizer": data.tokenizer,
            "cache_dir": data.cache_dir,
        }
        processor = ProcessorFactory().get_processor(
            file_path=data.markdown_path, file_type="md", filename=data.filename, **kwargs
        )
        docs, next_rag_start_index, is_last_md_chunk = await processor.process()

        logger.info({
            "message": "Processed chunks",
            "docs": len(docs),
            "next_rag_start_index": next_rag_start_index,
            "is_last_md_chunk": is_last_md_chunk,
        })

        # TODO: process

        if not is_last_md_chunk:
            # More chunks remain in THIS markdown file -> keep chunking it.
            await RMQProducerHelper.produce_markdown(cp, ps.MarkdownProcessParams(
                markdown_path=data.markdown_path,
                file_chunk_number=data.file_chunk_number + 1,
                filename=data.filename,
                rag_chunk_start_index=next_rag_start_index,
                is_last=is_last_md_chunk,
                max_chunk_size_mb=data.max_chunk_size_mb,
                tokenizer=data.tokenizer,
                cache_dir=data.cache_dir,
                is_ocr_part=data.is_ocr_part,
                ocr_params=data.ocr_params,
            ))
            return

        # This markdown file's chunks are exhausted. If it was produced as part
        # of an OCR pipeline and there are more pages left to OCR, resume OCR.
        if data.is_ocr_part and data.ocr_params is not None and not data.ocr_params.is_last_ocr_batch:
            resume_params = data.ocr_params.model_copy(
                update={"rag_chunk_start_index": next_rag_start_index}
            )
            await RMQProducerHelper.produce_image(cp, resume_params)
            return

        if data.is_ocr_part and data.ocr_params is not None and data.ocr_params.is_last_ocr_batch:
            # TODO: status update
            pass

    @staticmethod
    async def handle_yaml(cp: ps.CommonParams, data: ps.YamlProcessParams):
        logger.info({"message": "Processing yaml", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "filename": data.filename, "start_object": data.start_object, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "start_object": data.start_object,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "objects_per_buffer": data.objects_per_buffer,
            "group_size": data.group_size,
            "max_group_size": data.max_group_size
        }

        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="yaml", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_yaml(cp, data.model_copy(update={
                "start_object": data.start_object + (data.objects_per_buffer or 500),  # add objects per buffer
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_docx(cp: ps.CommonParams, data: ps.DocxProcessParams):
        logger.info({"message": "Processing docx", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "filename": data.filename, "file_chunk_number": data.file_chunk_number, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "chunk_number": data.file_chunk_number,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "pages_per_batch": data.pages_per_batch,
            "rag_chunk_size": data.rag_chunk_size,
            "rag_chunk_overlap": data.rag_chunk_overlap,
            "tail_carry_chars": data.tail_carry_chars
        }

        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="docx", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_docx(cp, data.model_copy(update={
                "file_chunk_number": data.file_chunk_number + 1,  # Increment chunk number
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_excel(cp: ps.CommonParams, data: ps.ExcelProcessParams):
        logger.info({"message": "Processing excel", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "filename": data.filename, "start_row": data.start_row, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "start_row": data.start_row,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "rows_per_io_buffer": data.rows_per_io_buffer,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "group_size": data.group_size,
            "max_group_size": data.max_group_size,
            "sheet": data.sheet
        }

        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="excel", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_excel(cp, data.model_copy(update={
                "start_row": data.start_row + data.rows_per_io_buffer,  # adding rows_per_io_buffer
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_code(cp: ps.CommonParams, data: ps.CodeProcessParams):
        logger.info({"message": "Processing code file", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "file_chunk_number": data.file_chunk_number, "filename": data.filename, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "chunk_number": data.file_chunk_number,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "language": data.language,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "rag_chunk_size": data.rag_chunk_size,
            "rag_chunk_overlap": data.rag_chunk_overlap,
            "tail_carry_chars": data.tail_carry_chars
        }

        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="code", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_code(cp, data.model_copy(update={
                "file_chunk_number": data.file_chunk_number + 1,  # Increment chunk number
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_ppt(cp: ps.CommonParams, data: ps.PptxProcessParams):
        logger.info({"message": "Processing ppt", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "file_chunk_number": data.file_chunk_number, "filename": data.filename, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "chunk_number": data.file_chunk_number,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "pages_per_batch": data.pages_per_batch,
            "rag_chunk_size": data.rag_chunk_size,
            "rag_chunk_overlap": data.rag_chunk_overlap
        }

        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="pptx", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_ppt(cp, data.model_copy(update={
                "file_chunk_number": data.file_chunk_number + 1,  # Increment chunk number
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_html(cp: ps.CommonParams, data: ps.HtmlProcessParams):
        logger.info({"message": "Processing html", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "start_unit": data.start_unit, "filename": data.filename, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "start_unit": data.start_unit,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "rows_per_io_buffer": data.rows_per_io_buffer,
            "units_per_buffer": data.units_per_buffer,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "group_size": data.group_size,
            "max_group_size": data.max_group_size
        }

        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="html", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_html(cp, data.model_copy(update={
                "start_unit": data.start_unit + (data.units_per_buffer or 500),  # adding units_per_buffer to start_unit
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_csv(cp: ps.CommonParams, data: ps.CSVProcessParams):
        logger.info({"message": "Processing csv", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "filename": data.filename, "start_row": data.start_row, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "start_row": data.start_row,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "rows_per_io_buffer": data.rows_per_io_buffer,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "group_size": data.group_size,
            "max_group_size": data.max_group_size
        }

        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="csv", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_csv(cp, data.model_copy(update={
                "start_row": data.start_row + data.rows_per_io_buffer,  # adding rows_per_io_buffer
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last
            }))

    @staticmethod
    async def handle_image(cp: ps.CommonParams, data: ps.ImageProcessParams):
        ocr_processor_type = data.processor

        match ocr_processor_type.value:
            case "datalab":
                kwargs = {
                    "start_page": data.start_page,
                    "max_pages_per_chunk": data.max_pages_per_chunk,
                    "max_chunk_size_mb": data.max_chunk_size_mb,
                    "timeout": data.timeout,
                }
                enum_type = ocr_enum.DATALAB
            case "llamaparse":
                kwargs = {
                    "start_page": data.start_page,
                    "max_pages_per_chunk": data.max_pages_per_chunk,
                    "max_chunk_size_mb": data.max_chunk_size_mb,
                    "timeout": data.timeout,
                    "tier": data.llama_tier,
                    "version": data.llama_version,
                    "poll_interval": data.llama_poll_interval,
                }
                enum_type = ocr_enum.LAMMAPARSE
            case "mistral":
                kwargs = {
                    "start_page": data.start_page,
                    "max_pages_per_chunk": data.max_pages_per_chunk,
                    "max_chunk_size_mb": data.max_chunk_size_mb,
                    "timeout": data.timeout,
                }
                enum_type = ocr_enum.MISTRAL
            case _:
                raise ValueError(f"Invalid OCR processor type: {ocr_processor_type}")

        processor = OcrProcessorFactory.get_processor(
                enum_type, data.file_path, data.filename, data.api_key, **kwargs
            )
        md_path, next_page, is_last_ocr_batch = await processor.process()

        logger.info({
            "message": "OCR batch complete",
            "doc_id": cp.doc_id,
            "start_page": data.start_page,
            "next_page": next_page,
            "is_last_ocr_batch": is_last_ocr_batch,
            "md_path": str(md_path),
        })

        # Params needed to resume OCR *after* this batch's markdown is fully
        # chunked. Carried inside the markdown message so handle_md can trigger
        # the next OCR batch once it's done, instead of firing it from here.
        next_ocr_params = ps.ImageProcessParams(
            file_path=data.file_path,
            filename=data.filename,
            processor=ocr_processor_type,
            api_key=data.api_key,
            start_page=next_page,
            file_chunk_number=0,
            rag_chunk_start_index=data.rag_chunk_start_index,  # gets refreshed later
            is_last_ocr_batch=is_last_ocr_batch,
            max_pages_per_chunk=data.max_pages_per_chunk,
            max_chunk_size_mb=data.max_chunk_size_mb,
            timeout=data.timeout,
            llama_tier=data.llama_tier,
            llama_version=data.llama_version,
            llama_poll_interval=data.llama_poll_interval,
        )

        # IMPORTANT: always chunk this batch's markdown, whether or not this
        # was the final OCR batch. (Previously this was gated on `not is_last`,
        # which silently dropped the last batch's text.)
        md_processor = ps.MarkdownProcessParams(
            markdown_path=str(md_path),
            filename=md_path.name,
            file_chunk_number=0,
            rag_chunk_start_index=data.rag_chunk_start_index,
            is_last=False,  # placeholder; handle_md computes the real value from its own processor
            is_ocr_part=True,
            ocr_params=next_ocr_params,
        )
        await RMQProducerHelper.produce_markdown(cp, md_processor)

    @staticmethod
    async def handle_audio(cp: ps.CommonParams, data: ps.AudioProcessParams):
        entry = _AUDIO_PROVIDERS.get(data.processor.value)
        if entry is None:
            raise Exception(f"Unknown audio processor type: {data.processor}")

        provider_enum, param_map = entry
        kwargs = {kw: getattr(data, attr) for kw, attr in param_map.items()}

        processor = AudioProcessorFactory.get_processor(
            provider_enum, data.file_path, data.filename, data.api_key,
            data.file_chunk_number, data.rag_chunk_start_index,
            timeout=data.timeout, **kwargs,
        )
        docs, next_rag_start_index, is_last = await processor.process()

        # TODO: process docs

        if not is_last:
            # every provider-specific field is already on `data` and unchanged
            # between chunks -- only these three move.
            await RMQProducerHelper.produce_audio(cp, data.model_copy(update={
                "file_chunk_number": data.file_chunk_number + 1,
                "rag_chunk_start_index": next_rag_start_index,
                "is_last": is_last,
            }))
