from .llamaparse_processor import LlamaCloudOCRProcessor
from .mistral_processor import MistralOCRProcessor
from .datalab_processor import DatalabOCRProcessor
from .base import OCRProcessor
from enum import Enum


class ProcessorEnum(Enum):
    DATALAB = "datalab"
    MISTRAL = "mistral"
    LAMMAPARSE = "llamaparse"


class OcrProcessorFactory:
    def __init__(self):
        pass

    @staticmethod
    def get_processor(processor: ProcessorEnum, file_path: str, filename: str, api_key: str, **kwargs) -> OCRProcessor:
        if processor == ProcessorEnum.DATALAB:
            return OcrProcessorFactory._get_datalab_processor(file_path=file_path, filename=filename, api_key=api_key, **kwargs)
        elif processor == ProcessorEnum.MISTRAL:
            return OcrProcessorFactory._get_mistral_processor(file_path=file_path, filename=filename, api_key=api_key, **kwargs)
        elif processor == ProcessorEnum.LAMMAPARSE:
            return OcrProcessorFactory._get_llamaparse_processor(file_path=file_path, filename=filename, api_key=api_key, **kwargs)

    @staticmethod
    def _get_datalab_processor(file_path: str, filename: str, api_key: str, **kwargs) -> OCRProcessor:
        return DatalabOCRProcessor(file_path=file_path, filename=filename, api_key=api_key, **kwargs)

    @staticmethod
    def _get_mistral_processor(file_path: str, filename: str, api_key: str, **kwargs) -> OCRProcessor:
        return MistralOCRProcessor(file_path=file_path, filename=filename, api_key=api_key, **kwargs)

    @staticmethod
    def _get_llamaparse_processor(file_path: str, filename: str, api_key: str, **kwargs) -> OCRProcessor:
        return LlamaCloudOCRProcessor(file_path=file_path, filename=filename, api_key=api_key, **kwargs)
