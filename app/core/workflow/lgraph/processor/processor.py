from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from langchain_core.documents import Document


class Processor(ABC):
    """
    Abstract base class for processing a file and turning it into document chunks.
    This defines the 'Strategy' interface for handling different file types.
    """

    @abstractmethod
    def process(
        self, file_path: str, chunk_size: int, chunk_overlap: int, metadata: Optional[Dict[str, str | bool | int]] = None
    ) -> Dict[str, List[Document]]:
        """
        Loads a document from a file path, splits it into chunks,
        and returns a list of Document objects ready for ingestion.

        Args:
            file_path (str): The path to the document file.
            chunk_size (int): The target size for each document chunk.
            chunk_overlap (int): The amount of overlap between consecutive chunks.
            metadata (Optional[Dict[str, str | bool | int]]): Optional metadata for the document.

        Returns:
            List[Document]: A list of processed document chunks.
        """
        pass

    @abstractmethod
    def add_metadata_to_chunk(
        self,
        chunk: Document,
        metadata: Optional[Dict[str, str | bool | int]] = None,
    ) -> Document:
       pass
