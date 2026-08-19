from ..schemas.document_processing_schema import DocumentProcessingCreateSchema, DocumentProcessingUpdateSchema, ProcessingStatus
from ..schemas.processor_schema import OCRProcessor, AudioProcessor, VideoProcessor
from ..services.document_processing_service import DocumentProcessingService
from ..processor.text.processor_helper import get_language_from_extension
from ..schemas.project_config_schema import ProjectConfigDetailGetSchema
from ..services.project_variables_service import ProjectVariableService
from ..services.project_config_service import ProjectConfigService
from ..schemas.project_variables_schema import ProjectVariableBase
from ..schemas.document_schema import DocumentGetSchema
from ..helpers.minio_helper import MinioHelper
from ..schemas import processor_schema as ps
from .temp_helper import get_temp_path
from app.utils.logger import logger


class ProcessHelper:
    def __init__(self):
        pass

    @staticmethod
    async def _build_ocr_params(
        file_path: str,
        filename: str,
        file_chunk_number: int,
        rag_chunk_start_index: int,
        project_config: ProjectConfigDetailGetSchema,
        project_variables: ProjectVariableBase
    ) -> ps.OCRProcessParams:
        """Shared OCR params builder — used by IMAGE, and by PDF/DOC/PPT
        when is_ocr_needed=True."""
        ocr_model = project_config.ocr_model
        if ocr_model is None:
            raise Exception("OCR model not configured for project")
        ocr_model_credential = project_config.ocr_model_credential
        if ocr_model_credential is None:
            raise Exception("OCR model credential not configured for project")

        if ocr_model.provider == "datalab":
            processor = OCRProcessor.DATALAB
        elif ocr_model.provider == "mistral":
            processor = OCRProcessor.MISTRAl
        elif ocr_model.provider == "llamaparse":
            processor = OCRProcessor.LAMMAPARSE
        else:
            raise Exception("OCR model provider not supported")

        return ps.OCRProcessParams(
            file_path=file_path,
            filename=filename,
            processor=processor,
            api_key=ocr_model_credential.api_key,
            start_page=0,
            is_last_ocr_batch=False,
            rag_chunk_start_index=rag_chunk_start_index,
            file_chunk_number=file_chunk_number,
            max_chunk_size_mb=project_variables.max_chunk_size_mb,
            max_pages_per_chunk=project_variables.max_pages_per_batch
        )

    @staticmethod
    async def _build_audio_params(
        file_path: str,
        filename: str,
        file_chunk_number: int,
        rag_chunk_start_index: int,
        project_config: ProjectConfigDetailGetSchema,
        project_variables: ProjectVariableBase
    ) -> ps.AudioProcessParams:
        audio_model = project_config.audio_model
        if audio_model is None:
            raise Exception("Audio model not configured for project")
        if project_config.audio_model_credential is None:
            raise Exception("Audio model credential not configured for project")

        if audio_model.provider == "assemblyai":
            processor = AudioProcessor.ASSEMBLYAI
        elif audio_model.provider == "deepgram":
            processor = AudioProcessor.DEEPGRAM
        elif audio_model.provider == "gladia":
            processor = AudioProcessor.GLADIA
        elif audio_model.provider == "groq":
            processor = AudioProcessor.GROQ
        elif audio_model.provider == "elevenlabs":
            processor = AudioProcessor.ELEVENLABS
        else:
            raise Exception("Audio model provider not supported")

        return ps.AudioProcessParams(
            file_path=file_path,
            filename=filename,
            processor=processor,
            api_key=project_config.audio_model_credential.api_key,
            file_chunk_number=file_chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            is_last=False,
            segment_duration_min=project_variables.audio_segment_duration_minutes,
            max_time_per_rag_chunk_min=project_variables.audio_max_duration_per_rag_chunk,
            max_words_per_rag_chunk=project_variables.audio_max_words_per_rag_chunk
        )

    @staticmethod
    async def _build_video_params(
        file_path: str,
        filename: str,
        file_chunk_number: int,
        rag_chunk_start_index: int,
        project_config: ProjectConfigDetailGetSchema,
        project_variables: ProjectVariableBase
    ) -> ps.VideoProcessParams:
        video_model = project_config.video_model
        if video_model is None:
            raise Exception("Video model not configured for project")
        if project_config.video_model_credential is None:
            raise Exception("Video model credential not configured for project")

        if video_model.provider == "gemini":
            processor = VideoProcessor.GEMINI
        elif video_model.provider == "twelvelabs":
            processor = VideoProcessor.TWELVELABS
        else:
            raise Exception("Video model provider not supported")

        return ps.VideoProcessParams(
            file_path=file_path,
            filename=filename,
            processor=processor,
            api_key=project_config.video_model_credential.api_key,
            file_chunk_number=file_chunk_number,
            rag_chunk_start_index=1 if rag_chunk_start_index == 0 else rag_chunk_start_index,  # since 0 is reserved for overview
            is_last=False,
            chunk_duration_min=project_variables.video_segment_duration_minutes,
            overlap_min=project_variables.video_overlap_minutes,
            max_duration_per_rag_chunk_sec=project_variables.video_max_duration_per_rag_chunk,
            max_words_per_rag_chunk=project_variables.video_max_words_per_rag_chunk
        )

    @staticmethod
    async def get_process_params(document: DocumentGetSchema) -> ps.ProcessParams:
        try:
            file_type = ps.get_file_type(document.name)
            if file_type is None:
                raise Exception("File type not supported")

            project_variables = await ProjectVariableService(
                org_id=document.org_id, project_id=document.project_id
            ).get_by_project()
            if project_variables is None:
                raise Exception("Project variables not found")

            pp: ps.ProcessParams = ps.ProcessParams(
                org_id=document.org_id,
                project_id=document.project_id,
                doc_id=document.id,
                doc_readable_id=document.readable_id,
                file_type=file_type,
                filename=document.name,
                project_variables=project_variables
            )

            max_chunk_size_mb = project_variables.max_chunk_size_mb
            chunk_size = project_variables.chunk_size
            chunk_overlap = project_variables.chunk_overlap
            tail_carry_chars = project_variables.tail_carry_chars
            max_pages_per_batch = project_variables.max_pages_per_batch
            group_size = project_variables.group_size_for_rag_chunk
            max_group_size = project_variables.max_group_size_for_rag_chunk
            objects_per_buffer = project_variables.objects_per_buffer

            download_path = get_temp_path()

            file_path = await MinioHelper(document.org_id, document.project_id).download_file(
                document.bucket, document.key, download_path, document.name
            )

            project_config = await ProjectConfigService(
                org_id=document.org_id, project_id=document.project_id
            ).get_with_details_by_project(is_external_call=False)
            if project_config is None:
                raise Exception("Project config not found")

            file_chunk_number = 0
            rag_chunk_start_index = 0
            start_row = 0
            start_object = 0
            start_unit = 0

            document_processing_service = DocumentProcessingService(
                org_id=document.org_id, 
                project_id=document.project_id, 
                document_id=document.id
            )
            document_processing_state = await document_processing_service.get_by_document()

            if document_processing_state is None:
                logger.info({"message": "Document processing state creating......"})
                await document_processing_service.create(c=DocumentProcessingCreateSchema(
                    document_id=document.id,
                    status=ProcessingStatus.PROCESSING,
                    last_file_chunk_number=-1,
                    next_rag_start_index=0,
                    next_start_row=0,
                    next_start_object=0,
                    next_start_unit=0
                ))
            else:
                logger.info({
                    "message": "Resuming document processing", 
                    "last_chunk": document_processing_state.last_file_chunk_number
                })
                # If it failed/stopped on the very first try, last_file_chunk_number is -1.
                # -1 + 1 = 0 (Starts perfectly at the beginning)
                # If it failed after chunk 5, last_file_chunk_number is 5.
                # 5 + 1 = 6 (Starts perfectly at chunk 6)
                file_chunk_number = document_processing_state.last_file_chunk_number + 1
                rag_chunk_start_index = document_processing_state.next_rag_start_index

                start_row = document_processing_state.next_start_row
                start_object = document_processing_state.next_start_object
                start_unit = document_processing_state.next_start_unit

                # Update the status to PROCESSING if it was previously FAILED or PENDING
                if document_processing_state.status != ProcessingStatus.PROCESSING:
                    await document_processing_service.update(
                        u=DocumentProcessingUpdateSchema(status=ProcessingStatus.PROCESSING)
                    )

            # logger.info({"project_config": project_config})

            # File types that are allowed to go through the OCR pipeline
            # instead of their normal parser, when is_ocr_needed is True.
            OCR_ELIGIBLE_TYPES = {ps.FileType.PDF, ps.FileType.DOC, ps.FileType.PPT}

            if file_type in OCR_ELIGIBLE_TYPES and document.is_ocr_needed:
                pp.ocr_params = await ProcessHelper._build_ocr_params(
                    file_path=file_path,
                    filename=document.name,
                    file_chunk_number=file_chunk_number,
                    rag_chunk_start_index=rag_chunk_start_index,
                    project_config=project_config,
                    project_variables=project_variables
                )

            elif file_type is ps.FileType.TEXT:
                pp.txt_params = ps.TxtProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    file_chunk_number=file_chunk_number,
                    is_last=False,
                    max_chunk_size_mb=max_chunk_size_mb,
                    rag_chunk_size=chunk_size,
                    rag_chunk_overlap=chunk_overlap,
                    tail_carry_chars=tail_carry_chars
                )

            elif file_type is ps.FileType.PDF:
                pp.pdf_params = ps.PdfProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    file_chunk_number=file_chunk_number,
                    is_last=False,
                    is_ocr_needed=document.is_ocr_needed,
                    pages_per_batch=max_pages_per_batch,
                    rag_chunk_size=chunk_size,
                    rag_chunk_overlap=chunk_overlap,
                    tail_carry_chars=tail_carry_chars
                )
            elif file_type is ps.FileType.MARKDOWN:
                pp.md_params = ps.MarkdownProcessParams(
                    markdown_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    file_chunk_number=file_chunk_number,
                    is_last=False,
                    max_chunk_size_mb=project_variables.max_chunk_size_mb
                )
            elif file_type is ps.FileType.DOC:
                pp.docx_params = ps.DocxProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    file_chunk_number=file_chunk_number,
                    is_last=False,
                    is_ocr_needed=document.is_ocr_needed,
                    pages_per_batch=max_pages_per_batch,
                    rag_chunk_size=chunk_size,
                    rag_chunk_overlap=chunk_overlap,
                    tail_carry_chars=tail_carry_chars
                )
            elif file_type is ps.FileType.PPT:
                pp.ppt_params = ps.PptxProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    file_chunk_number=file_chunk_number,
                    is_last=False,
                    is_ocr_needed=document.is_ocr_needed,
                    pages_per_batch=max_pages_per_batch,
                    rag_chunk_size=chunk_size,
                    rag_chunk_overlap=chunk_overlap,
                )
            elif file_type is ps.FileType.EXCEL:
                pp.excel_params = ps.ExcelProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    start_row=start_row,
                    is_last=False,
                    max_chunk_size_mb=max_chunk_size_mb,
                    group_size=group_size,
                    max_group_size=max_group_size
                )
            elif file_type is ps.FileType.HTML:
                pp.html_params = ps.HtmlProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    start_unit=start_unit,
                    is_last=False,
                    max_chunk_size_mb=max_chunk_size_mb,
                    group_size=group_size,
                    max_group_size=max_group_size
                )
            elif file_type is ps.FileType.JSON:
                pp.json_params = ps.JsonProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    start_object=start_object,
                    is_last=False,
                    max_chunk_size_mb=max_chunk_size_mb,
                    group_size=group_size,
                    max_group_size=max_group_size
                )
            elif file_type is ps.FileType.CSV:
                pp.csv_params = ps.CSVProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    start_row=start_row,
                    is_last=False,
                    max_chunk_size_mb=max_chunk_size_mb,
                    group_size=group_size,
                    max_group_size=max_group_size
                )
            elif file_type is ps.FileType.XML:
                pp.xml_params = ps.XmlProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=rag_chunk_start_index,
                    start_object=start_object,
                    is_last=False,
                    max_chunk_size_mb=max_chunk_size_mb,
                    group_size=group_size,
                    objects_per_buffer=objects_per_buffer,
                    max_group_size=max_group_size
                )

            elif file_type is ps.FileType.CODE:
                language = get_language_from_extension(document.name)
                if language is None:
                    raise Exception("Language not supported")
                pp.code_params = ps.CodeProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    file_chunk_number=file_chunk_number,
                    rag_chunk_start_index=rag_chunk_start_index,
                    is_last=False,
                    language=language,
                    max_chunk_size_mb=max_chunk_size_mb,
                    rag_chunk_size=chunk_size,
                    rag_chunk_overlap=chunk_overlap,
                    tail_carry_chars=tail_carry_chars
                )

            elif file_type is ps.FileType.YAML:
                pp.yaml_params = ps.YamlProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    start_object=start_object,
                    rag_chunk_start_index=rag_chunk_start_index,
                    is_last=False,
                    objects_per_buffer=objects_per_buffer,
                    max_chunk_size_mb=max_chunk_size_mb,
                    group_size=group_size,
                    max_group_size=max_group_size
                )

            elif file_type is ps.FileType.AUDIO:
                pp.audio_params = await ProcessHelper._build_audio_params(
                    file_path=file_path,
                    filename=document.name,
                    file_chunk_number=file_chunk_number,
                    rag_chunk_start_index=rag_chunk_start_index,
                    project_config=project_config,
                    project_variables=project_variables,
                )

            elif file_type is ps.FileType.IMAGE:
                pp.ocr_params = await ProcessHelper._build_ocr_params(
                    file_path=file_path,
                    filename=document.name,
                    file_chunk_number=file_chunk_number,
                    rag_chunk_start_index=rag_chunk_start_index,
                    project_config=project_config,
                    project_variables=project_variables
                )

            elif file_type is ps.FileType.VIDEO:
                pp.video_params = await ProcessHelper._build_video_params(
                    file_path=file_path,
                    filename=document.name,
                    file_chunk_number=file_chunk_number,
                    rag_chunk_start_index=rag_chunk_start_index,
                    project_config=project_config,
                    project_variables=project_variables
                )
            print("process params: ", pp.model_dump(mode="json", exclude_unset=True, exclude_none=True))
            return pp
        except Exception as e:
            logger.error({"message": "Failed to get process params", "error": str(e)})
            raise e
