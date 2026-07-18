from .code_processor import CodeProcessor, is_code_file, get_language_from_extension
from .markdown_processor import MarkdownProcessor
from langchain_text_splitters import Language
from .excel_processor import ExcelProcessor
from .text_processor import TextProcessor
from .json_processor import JsonProcessor
from .html_processor import HTMLProcessor
from .yaml_processor import YAMLProcessor
from .pptx_processor import PPTXProcessor
from .docx_processor import DOCXProcessor
from .xml_processor import XMLProcessor
from .csv_processor import CSVProcessor
from .processor import Processor
from app.config.env import Env
from typing import Any


class ProcessorFactory:

    @staticmethod
    def get_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:

        safe_file_type = file_type.lower() if file_type else ""
        lower_path = file_path.lower()

        if safe_file_type in ("text", "txt") or lower_path.endswith(".txt"):
            return ProcessorFactory._text_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type in ("markdown", "md") or lower_path.endswith(".md"):
            return ProcessorFactory._markdown_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type in ("excel", "xlsx", "xls") or lower_path.endswith((".xlsx", ".xls")):
            return ProcessorFactory._excel_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type == "json" or lower_path.endswith(".json"):
            return ProcessorFactory._json_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type in ("html", "htm") or lower_path.endswith((".html", ".htm")):
            return ProcessorFactory._html_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type in ("yaml", "yml") or lower_path.endswith((".yaml", ".yml")):
            return ProcessorFactory._yaml_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type in ("pptx", "ppt", "powerpoint") or lower_path.endswith((".pptx", ".ppt", ".pptm", ".potx", ".pot")):
            return ProcessorFactory._pptx_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type in ("docx", "doc", "word") or lower_path.endswith((".docx", ".doc", ".docm", ".dotx", ".dot")):
            return ProcessorFactory._docx_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type == "xml" or lower_path.endswith(".xml"):
            return ProcessorFactory._xml_file_processor(file_path, file_type, filename, **kwargs)

        elif safe_file_type == "csv" or lower_path.endswith(".csv"):
            return ProcessorFactory._csv_file_processor(file_path, file_type, filename, **kwargs)

        elif is_code_file(file_path):
            language = get_language_from_extension(file_path)
            if language:
                return ProcessorFactory._code_file_processor(file_path, file_type, filename, language, **kwargs)
            else:
                raise ValueError(f"Unsupported code file type: {file_type}")

        raise ValueError(f"Unsupported file type: {file_type}")

    @staticmethod
    def _json_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # start_object: int,                  # 0-based object index to start from
        # rag_chunk_start_index: int,         # absolute RAG chunk index to continue from
        # objects_per_buffer: int = 500,      # max objects to read per batch
        # max_chunk_size_mb: float = 50,      # hard size cap — stops before breaching
        # group_size: int = 10,              # target objects per RAG chunk
        # max_group_size: int = 20,          # hard cap — oversized clusters get split

        start_object = kwargs.get("start_object")
        if not start_object and start_object != 0:
            raise ValueError("start_object is required for json files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for json files")

        return JsonProcessor(
            file_path=file_path,
            filename=filename,
            start_object=start_object,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )

    @staticmethod
    def _html_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # start_unit: int,                  # 0-based index into extracted units (content blocks + table rows)
        # rag_chunk_start_index: int,       # absolute RAG chunk index to continue from
        # units_per_buffer: int = 500,      # max units to read per batch
        # max_chunk_size_mb: float = 50,
        # group_size: int = 10,             # target units per RAG chunk
        # max_group_size: int = 20,         # hard cap — oversized clusters get split

        start_unit = kwargs.get("start_unit")
        if not start_unit and start_unit != 0:
            raise ValueError("start_unit is required for html files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for html files")

        return HTMLProcessor(
            file_path=file_path,
            filename=filename,
            start_unit=start_unit,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )

    @staticmethod
    def _yaml_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # start_object: int,
        # rag_chunk_start_index: int,
        # objects_per_buffer: int = 500,
        # max_chunk_size_mb: float = 50,
        # group_size: int = 10,
        # max_group_size: int = 20,
        # scan_lines: int = 100,

        start_object = kwargs.get("start_object")
        if not start_object and start_object != 0:
            raise ValueError("start_object is required for yaml files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for yaml files")

        return YAMLProcessor(
            file_path=file_path,
            filename=filename,
            start_object=start_object,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )

    @staticmethod
    def _pptx_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # chunk_number: int,
        # rag_chunk_start_index: int,
        # pages_per_batch: int = 20,          # maps directly to slides_per_batch
        # rag_chunk_size: int = Env.CHUNK_SIZE,
        # rag_chunk_overlap: int = Env.CHUNK_OVERLAP,

        chunk_number = kwargs.get("chunk_number")
        if not chunk_number and chunk_number != 0:
            raise ValueError("chunk_number is required for pptx files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for pptx files")

        return PPTXProcessor(
            file_path=file_path,
            filename=filename,
            chunk_number=chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )

    @staticmethod
    def _docx_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # chunk_number: int,
        # rag_chunk_start_index: int,
        # pages_per_batch: int = 20,          # treated as paragraphs_per_batch for DOCX
        # rag_chunk_size: int = Env.CHUNK_SIZE,
        # rag_chunk_overlap: int = Env.CHUNK_OVERLAP,
        # tail_carry_chars: int = 500,

        chunk_number = kwargs.get("chunk_number")
        if not chunk_number and chunk_number != 0:
            raise ValueError("chunk_number is required for docx files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for docx files")

        return DOCXProcessor(
            file_path=file_path,
            filename=filename,
            chunk_number=chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )

    @staticmethod
    def _xml_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # start_object: int,                      # 0-based record index to start from
        # rag_chunk_start_index: int,             # absolute RAG chunk index to continue from
        # record_tag: Optional[str] = None,       # repeating element tag — auto-detected if None
        # objects_per_buffer: int = 500,          # max records per batch
        # max_chunk_size_mb: float = 50,
        # group_size: int = 10,                   # target records per RAG chunk
        # max_group_size: int = 20,               # hard cap — oversized clusters get split

        start_object = kwargs.get("start_object")
        if not start_object and start_object != 0:
            raise ValueError("start_object is required for xml files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for xml files")

        return XMLProcessor(
            file_path=file_path,
            filename=filename,
            start_object=start_object,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )

    @staticmethod
    def _csv_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # start_row: int,                   # 0-based row index (excluding header)
        # rag_chunk_start_index: int,       # absolute RAG chunk index to continue from
        # rows_per_io_buffer: int = 500,    # rows to read from disk at once (IO buffer)
        # max_chunk_size_mb: float = 50,
        # group_size: int = 10,             # target rows per RAG chunk
        # max_group_size: int = 20,         # oversized clusters get split at this threshold

        start_row = kwargs.get("start_row")
        if not start_row and start_row != 0:
            raise ValueError("start_row is required for csv files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for csv files")

        return CSVProcessor(
            file_path=file_path,
            filename=filename,
            start_row=start_row,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )

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
            markdown_path=file_path,
            filename=filename,
            chunk_number=chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            max_chunk_size_mb=kwargs.get("max_chunk_size_mb", 50),
        )

    @staticmethod
    def _code_file_processor(file_path: str, file_type: str, filename: str, language: Language, **kwargs: Any) -> Processor:
        chunk_number = kwargs.get("chunk_number")
        if not chunk_number and chunk_number != 0:
            raise ValueError("chunk_number is required for code files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for code files")

        return CodeProcessor(
            file_path=file_path,
            filename=filename,
            chunk_number=chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            language=language,
            max_chunk_size_mb=kwargs.get("max_chunk_size_mb", 50),
            rag_chunk_size=kwargs.get("rag_chunk_size_mb", Env.CHUNK_SIZE),
            rag_chunk_overlap=kwargs.get("rag_chunk_overlap", Env.CHUNK_OVERLAP),
            tail_carry_chars=kwargs.get("tail_carry_chars", 500)
        )

    @staticmethod
    def _excel_file_processor(file_path: str, file_type: str, filename: str, **kwargs: Any) -> Processor:
        # file_path: str,
        # filename: str,
        # start_row: int,                        # 0-based row index (excluding header)
        # rag_chunk_start_index: int,            # absolute RAG chunk index to continue from
        # sheet: Optional[str | int] = 0,        # sheet name or 0-based index (default: first sheet)
        # rows_per_io_buffer: int = 500,         # rows to read from disk at once
        # max_chunk_size_mb: float = 50,
        # group_size: int = 10,                  # target rows per RAG chunk
        # max_group_size: int = 20, 

        start_row = kwargs.get("start_row")
        if not start_row and start_row != 0:
            raise ValueError("start_row is required for code files")

        rag_chunk_start_index = kwargs.get("rag_chunk_start_index")
        if not rag_chunk_start_index and rag_chunk_start_index != 0:
            raise ValueError("rag_chunk_start_index is required for code files")

        return ExcelProcessor(
            file_path=file_path,
            filename=filename,
            start_row=start_row,
            rag_chunk_start_index=rag_chunk_start_index,
            **kwargs
        )
