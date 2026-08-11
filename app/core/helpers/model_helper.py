from ..services.project_config_service import ProjectConfigService
from ..schemas.processor_schema import FileType, get_file_type
import uuid


class ModelHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.project_config_service = ProjectConfigService(org_id=self.org_id, project_id=self.project_id)

    async def check_model_check(self, filename: str, is_ocr_enabled: bool = False) -> bool:
        try:
            file_type = get_file_type(filename)
            if file_type is None:
                raise Exception("Unknown file type")

            project_config = await self.project_config_service.get_with_details_by_project()
            if project_config is None:
                raise Exception("Project config not found for Project with id " + str(self.project_id))

            if file_type is FileType.VIDEO:
                if project_config.video_model is None:
                    raise Exception("Video model is not configured for Project with id " + str(self.project_id))
                if project_config.video_model_credential is None:
                    raise Exception("Video model credential is not configured for Project with id " + str(self.project_id))

            if file_type is FileType.AUDIO:
                if project_config.audio_model is None:
                    raise Exception("Audio model is not configured for Project with id " + str(self.project_id))
                if project_config.audio_model_credential is None:
                    raise Exception("Audio model credential is not configured for Project with id " + str(self.project_id))

            if file_type is FileType.IMAGE:
                if project_config.ocr_model is None:
                    raise Exception("OCR model is not configured for Project with id " + str(self.project_id))
                if project_config.ocr_model_credential is None:
                    raise Exception("OCR model credential is not configured for Project with id " + str(self.project_id))

            if file_type in [FileType.PDF, FileType.PPT, FileType.DOC] and is_ocr_enabled:
                if project_config.ocr_model is None:
                    raise Exception("OCR model is not configured for Project with id " + str(self.project_id))
                if project_config.ocr_model_credential is None:
                    raise Exception("OCR model credential is not configured for Project with id " + str(self.project_id))
            return True
        except Exception as e:
            raise e
