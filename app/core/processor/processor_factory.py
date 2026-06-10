from .markdown_processor import MarkdownProcessor
from .text_processor import TextProcessor
from .processor import Processor
from app.config.env import Env
from typing import Any


class ProcessorFactory:

    @staticmethod
    def get_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:

        safe_file_type = file_type.lower() if file_type else ""

        if safe_file_type in ("text", "txt") or file_path.lower().endswith(".txt"):
            return ProcessorFactory._text_file_processor(file_path, file_type, filename, **kwargs)
        elif safe_file_type in ("markdown", "md") or file_path.lower().endswith(".md"):
            return ProcessorFactory._markdown_file_processor(file_path, file_type, filename, **kwargs)

        raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _text_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        chunk_number = kwargs.get("chunk_number")
        if not chunk_number and chunk_number != 0:
            raise ValueError("chunk_number is required for text files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for text files")

        return TextProcessor(
            file_path=file_path,
            filename=filename,
            chunk_number=chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            max_chunk_size_mb=kwargs.get("max_chunk_size_mb", 50),
            rag_chunk_size=kwargs.get("rag_chunk_size_mb", Env.CHUNK_SIZE),
            rag_chunk_overlap=kwargs.get("rag_chunk_overlap", Env.CHUNK_OVERLAP),
            tail_carry_chars=kwargs.get("tail_carry_chars", 500)
        )

    @staticmethod
    def _markdown_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        chunk_number = kwargs.get("chunk_number")
        if not chunk_number and chunk_number != 0:
            raise ValueError("chunk_number is required for markdown files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for markdown files")

        return MarkdownProcessor(
            file_path=file_path,
            filename=filename,
            chunk_number=chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            max_chunk_size_mb=kwargs.get("max_chunk_size_mb", 50),
            rag_chunk_size=kwargs.get("rag_chunk_size_mb", Env.CHUNK_SIZE),
            rag_chunk_overlap=kwargs.get("rag_chunk_overlap", Env.CHUNK_OVERLAP),
            tail_carry_chars=kwargs.get("tail_carry_chars", 500)
        )
