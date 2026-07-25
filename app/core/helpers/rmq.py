from ..processor.text.processor_factory import ProcessorFactory
from ..rabbitmq.producer import GMQDocumentProducer
from ..schemas import processor_schema as ps
from app.utils.logger import logger
import uuid


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

    # @staticmethod
    # async def produce_docx(cp: ps.CommonParams, docx: ps.DocxProcessParams):
    #     await GMQDocumentProducer.publish_to_processing_exchange(ps.ProcessParams(
    #                     org_id=cp.org_id,
    #                     project_id=cp.project_id,
    #                     doc_id=cp.doc_id,
    #                     file_type=cp.file_type,
    #                     filename=docx.filename,
    #                     docx_params=docx
    #         ))


class RMQHelper:
    @staticmethod
    async def handle_txt(cp: ps.CommonParams, data: ps.TxtProcessParams):
        logger.info({"message": "Processing text", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "file_chunk_number": data.file_chunk_number, "filename": data.filename, "rag_chunk_start_index": data.rag_chunk_start_index})

        kwargs = {
            "chunk_number": data.file_chunk_number,
            "rag_chunk_start_index": data.rag_chunk_start_index,
            "max_chunk_size_mb": data.max_chunk_size_mb,
            "rag_chunk_size_mb": data.rag_chunk_size_mb,
            "rag_chunk_overlap": data.rag_chunk_overlap,
            "tail_carry_chars": data.tail_carry_chars
        }
        processor = ProcessorFactory().get_processor(file_path=data.file_path, file_type="txt", filename=data.filename, **kwargs)
        docs, next_rag_start_index, is_last = await processor.process()

        logger.info({"message": "Processed chunks", "docs": len(docs), "next_rag_start_index": next_rag_start_index, "is_last": is_last})

        # TODO: Process

        if not is_last:
            await RMQProducerHelper.produce_txt(cp, ps.TxtProcessParams(
                file_path=data.file_path,
                file_chunk_number=data.file_chunk_number,
                filename=data.filename,
                rag_chunk_start_index=next_rag_start_index,
                is_last=is_last,
                max_chunk_size_mb=data.max_chunk_size_mb,
                rag_chunk_size_mb=data.rag_chunk_size_mb,
                rag_chunk_overlap=data.rag_chunk_overlap,
                tail_carry_chars=data.tail_carry_chars
            ))

    @staticmethod
    async def handle_json(cp: ps.CommonParams, data: ps.JsonProcessParams):
        logger.info({"message": "Processing text", "common_params": cp.model_dump(mode="json", exclude_none=True), "data": data.model_dump(mode="json", exclude_none=True), "file_path": data.file_path, "filename": data.filename, "rag_chunk_start_index": data.rag_chunk_start_index})

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
            await RMQProducerHelper.produce_json(cp, ps.JsonProcessParams(
                file_path=data.file_path,
                filename=data.filename,
                rag_chunk_start_index=next_rag_start_index,
                is_last=is_last,
                start_object=data.start_object + (data.objects_per_buffer or 500),
                max_chunk_size_mb=data.max_chunk_size_mb,
                objects_per_buffer=data.objects_per_buffer,
                group_size=data.group_size,
                max_group_size=data.max_group_size
            ))

    @staticmethod
    async def handle_xml(cp: ps.CommonParams, data: ps.XmlProcessParams):
        pass

    @staticmethod
    async def handle_pdf(cp: ps.CommonParams, data: ps.PdfProcessParams):
        pass

    @staticmethod
    async def handle_md(cp: ps.CommonParams, data: ps.MdProcessParams):
        pass

    @staticmethod
    async def handle_yaml(cp: ps.CommonParams, data: ps.YamlProcessParams):
        pass

    @staticmethod
    async def handle_docx(cp: ps.CommonParams, data: ps.DocxProcessParams):
        pass

    @staticmethod
    async def handle_excel(cp: ps.CommonParams, data: ps.ExcelProcessParams):
        pass

    @staticmethod
    async def handle_code(cp: ps.CommonParams, data: ps.CodeProcessParams):
        pass

    @staticmethod
    async def handle_ppt(cp: ps.CommonParams, data: ps.PptxProcessParams):
        pass

    @staticmethod
    async def handle_html(cp: ps.CommonParams, data: ps.HtmlProcessParams):
        pass

    @staticmethod
    async def handle_csv(cp: ps.CommonParams, data: ps.CSVProcessParams):
        pass

    @staticmethod
    async def handle_image(cp: ps.CommonParams, data: ps.ImageProcessParams):
        pass

    @staticmethod
    async def handle_audio(cp: ps.CommonParams, data: ps.AudioProcessParams):
        pass
