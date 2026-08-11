from ..processor.text.processor_helper import get_language_from_extension
from ..schemas.document_schema import DocumentGetSchema
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

            if file_type is ps.FileType.TEXT:
                pp.txt_params = ps.TxtProcessParams(
                    file_path=file_path,
                    filename=document.name,
                    rag_chunk_start_index=0,
                    file_chunk_number=0,
                    is_last=False
                )

            elif file_type is ps.FileType.PDF:
                pass
            elif file_type is ps.FileType.MARKDOWN:
                pass
            elif file_type is ps.FileType.DOC:
                pass
            elif file_type is ps.FileType.PPT:
                pass
            elif file_type is ps.FileType.EXCEL:
                pass
            elif file_type is ps.FileType.HTML:
                pass
            elif file_type is ps.FileType.JSON:
                pass
            elif file_type is ps.FileType.CSV:
                pass
            elif file_type is ps.FileType.XML:
                pass

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
                pass
            elif file_type is ps.FileType.AUDIO:
                pass
            elif file_type is ps.FileType.IMAGE:
                pass
            elif file_type is ps.FileType.VIDEO:
                pass

            return pp
        except Exception as e:
            logger.error({"message": "Failed to get process params", "error": str(e)})
            raise e
