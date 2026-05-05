from app.utils.logger import logger
from typing import List, Dict, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .processor import Processor


class PDFProcessor(Processor):
    def process(
        self, file_path: str, chunk_size: int, chunk_overlap: int, metadata: Optional[Dict[str, str | bool | int]] = None
    ) -> Dict[str, List[Document]]:
        try:
            loader = PyPDFLoader(file_path)
            pages = loader.load()

            if not pages:
                logger.warning(f"PyPDFLoader returned no pages for {file_path}.")
                return {"chunks": [], "classes": []}

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            chunks = text_splitter.split_documents(pages)

            for chunk in chunks:
                chunk = self.add_metadata_to_chunk(chunk, metadata)

            return {"chunks": chunks, "classes": []}
        except Exception as e:
            logger.error(f"Failed to process PDF {file_path}. Error: {e}")
            return {"chunks": [], "classes": []}

    def add_metadata_to_chunk(
        self,
        chunk: Document,
        metadata: Optional[Dict[str, str | bool | int]] = None,
    ) -> Document:
        try:
            if not metadata:
                return chunk

            # Ensure metadata exists on the document
            allowed_keys = ["source", "element_id"]
            filtered_metadata = {
                key: chunk.metadata.get(key)
                for key in allowed_keys
                if key in chunk.metadata
            }

            chunk.metadata = filtered_metadata or {}

            for k, v in metadata.items():
                chunk.metadata[k] = v

            return chunk

        except Exception as e:
            logger.error(
                {
                    "message": "error adding metadata to chunks",
                    "error": str(e),
                }
            )
            return chunk
