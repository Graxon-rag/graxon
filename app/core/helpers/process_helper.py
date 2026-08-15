from ..processor.text.processor_helper import get_language_from_extension
from ..services.project_config_service import ProjectConfigService
from ..schemas.document_schema import DocumentGetSchema
from ..schemas.processor_schema import OCRProcessor
from ..helpers.minio_helper import MinioHelper
from ..schemas import processor_schema as ps
from .temp_helper import get_temp_path
from app.utils.logger import logger


class ProcessHelper:
    def __init__(self):
        pass

    @staticmethod
    async def get_process_params(document: DocumentGetSchema) -> ps.ProcessParams:
        try:
            file_type = ps.get_file_type(document.name)
            if file_type is None:
                raise Exception("File type not supported")

            pp: ps.ProcessParams = ps.ProcessParams(
                org_id=document.org_id,
                project_id=document.project_id,
                doc_id=document.id,
                file_type=file_type,
                filename=document.name
            )

            download_path = get_temp_path()

            file_path = await MinioHelper(document.org_id, document.project_id).download_file(document.bucket, document.key, download_path, document.name)

            project_config = await ProjectConfigService(org_id=document.org_id, project_id=document.project_id).get_with_details_by_project(is_external_call=False)
            if project_config is None:
                raise Exception("Project config not found")

            if file_type is ps.FileType.TEXT:
                pp.txt_params = ps.TxtProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    file_chunk_number=0,
                    is_last=False
                )

            elif file_type is ps.FileType.PDF:
                pp.pdf_params = ps.PdfProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    file_chunk_number=0,
                    is_last=False,
                    is_ocr_needed=document.is_ocr_needed
                )
            elif file_type is ps.FileType.MARKDOWN:
                pp.md_params = ps.MarkdownProcessParams(
                    markdown_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    file_chunk_number=0,
                    is_last=False,
                )
            elif file_type is ps.FileType.DOC:
                pp.docx_params = ps.DocxProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    file_chunk_number=0,
                    is_last=False,
                    is_ocr_needed=document.is_ocr_needed
                )
            elif file_type is ps.FileType.PPT:
                pp.ppt_params = ps.PptxProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    file_chunk_number=0,
                    is_last=False,
                    is_ocr_needed=document.is_ocr_needed
                )
            elif file_type is ps.FileType.EXCEL:
                pp.excel_params = ps.ExcelProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    start_row=0,
                    is_last=False,
                )
            elif file_type is ps.FileType.HTML:
                pp.html_params = ps.HtmlProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    start_unit=0,
                    is_last=False
                )
            elif file_type is ps.FileType.JSON:
                pp.json_params = ps.JsonProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    start_object=0,
                    is_last=False
                )
            elif file_type is ps.FileType.CSV:
                pp.csv_params = ps.CSVProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    start_row=0,
                    is_last=False
                )
            elif file_type is ps.FileType.XML:
                pp.xml_params = ps.XmlProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    start_object=0,
                    is_last=False
                )

            elif file_type is ps.FileType.CODE:
                language = get_language_from_extension(document.name)
                if language is None:
                    raise Exception("Language not supported")
                pp.code_params = ps.CodeProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    file_chunk_number=0,
                    rag_chunk_start_index=0,
                    is_last=False,
                    language=language
                )

            elif file_type is ps.FileType.YAML:
                pp.yaml_params = ps.YamlProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    start_object=0,
                    rag_chunk_start_index=0,
                    is_last=False
                )

            elif file_type is ps.FileType.AUDIO:
                pass

            elif file_type is ps.FileType.IMAGE:
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
                pp.ocr_params = ps.OCRProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    processor=processor,
                    api_key=ocr_model_credential.api_key,
                    start_page=0,
                    is_last_ocr_batch=False,
                    rag_chunk_start_index=0,
                    file_chunk_number=0
                )

            elif file_type is ps.FileType.VIDEO:
                pass

            return pp
        except Exception as e:
            logger.error({"message": "Failed to get process params", "error": str(e)})
            raise e
