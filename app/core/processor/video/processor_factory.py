from .twelvelabs_processor import TwelveLabsVideoProcessor
from .base import VideoProcessor
from enum import Enum


class VideoProcessorEnum(str, Enum):
    TWELVELABS = "twelvelabs"
    GEMINI = "gemini"


class VideoProcessorFactory:
    def __init__(self):
        pass

    @staticmethod
    def get_processor(
        processor: VideoProcessorEnum,
        file_path: str,
        filename: str,
        api_key: str,
        file_chunk_number: int,
        rag_chunk_start_index: int,
        timeout: float = 60 * 10,
        **kwargs
    ) -> VideoProcessor:
        if processor == VideoProcessorEnum.TWELVELABS:
            return TwelveLabsVideoProcessor(file_path=file_path, filename=filename, api_key=api_key, file_chunk_number=file_chunk_number, rag_chunk_start_index=rag_chunk_start_index, timeout=timeout, **kwargs)
        elif processor == VideoProcessorEnum.GEMINI:
            raise NotImplementedError
        else:
            raise ValueError(f"Unknown video processor: {processor}")
