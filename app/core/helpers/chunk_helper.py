from ..workflow.document_workflow import DocumentWorkflow
from langchain_core.documents import Document
from ..schemas import processor_schema as ps
from ..schemas import chunk_schema as cs
from app.config.config import Config
from app.utils.logger import logger
from ..libs.id import IDLibs
from pathlib import Path
from typing import List
import json


class ChunkHelper:

    @staticmethod
    async def inject(cp: ps.CommonParams, docs: List[Document]):
        try:
            if len(docs) == 0:
                return

            chunks: List[cs.Chunk] = []
            for doc in docs:
                text = doc.page_content
                metadata = doc.metadata.copy()
                file_chunk_number = metadata.pop("file_chunk_number", None)
                chunk_number = metadata.pop("rag_chunk_number", None)

                chunk = cs.Chunk(
                    chunk_id=IDLibs.generate_chunk_id(cp.doc_readable_id, chunk_number),
                    chunk_number=chunk_number,
                    text=text,
                    file_chunk_number=file_chunk_number,
                    metadata=metadata,
                )
                chunks.append(chunk)

            if Config.is_dev_env() or Config.is_test_env():
                ChunkHelper._save_to_debug(cp, chunks)

            result = await DocumentWorkflow(cp.org_id, cp.project_id).process(cp, chunks)
            return result
        except Exception as e:
            logger.error({"message": "Failed to process document", "error": str(e)})
            raise e

    @staticmethod
    def _save_to_debug(cp: ps.CommonParams, chunks: List[cs.Chunk]):
        # Ensure debug/chunks directory exists
        debug_dir = Path("debug/chunks")
        debug_dir.mkdir(parents=True, exist_ok=True)

        file_path = debug_dir / f"{cp.doc_id}.json"

        # Serialize Pydantic/dataclass models to dictionaries
        new_records = [
            chunk.model_dump()
            if hasattr(chunk, "model_dump")
            else chunk.dict()
            if hasattr(chunk, "dict")
            else chunk.__dict__
            for chunk in chunks
        ]

        # Load existing chunks if file exists, then append
        existing_data = []
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        existing_data = content
            except json.JSONDecodeError:
                existing_data = []

        existing_data.extend(new_records)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
