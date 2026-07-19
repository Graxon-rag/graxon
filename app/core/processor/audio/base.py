from langchain_core.documents import Document
from abc import ABC, abstractmethod
from typing import Tuple, List


class AudioProcessor(ABC):
    """
    Abstract base class for audio processors.

    An AudioProcessor defines the interface for converting an audio source
    into a sequence of LangChain ``Document`` objects suitable for downstream
    processing such as indexing, retrieval, or RAG pipelines.

    Implementations are responsible for handling the complete processing
    workflow, including tasks such as audio segmentation, transcription,
    speaker diarization, chunking, and metadata generation as required.
    """

    @abstractmethod
    async def process(self) -> Tuple[List[Document], int, bool]:
        """
        Process an audio source into LangChain documents.

        Returns:
            Tuple[List[Document], int, bool]:
                A tuple containing:
                - List[Document]: Documents generated from the processed audio.
                - int: Index of the next chunk/document to continue processing from.
                - bool: True if the processed input represents the final segment,
                otherwise False.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError
