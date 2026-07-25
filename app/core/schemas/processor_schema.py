from typing import Optional, List, Dict, Any, Literal
from langchain_text_splitters import Language
from pydantic import BaseModel, Field
from app.config.env import Env
from enum import Enum
import uuid


class OCRProcessor(str, Enum):
    MISTRAl = "mistral"
    DATALAB = "datalab"
    LAMMAPARSE = "llamaparse"


class AudioProcessor(str, Enum):
    DEEPGRAM = "deepgram"
    GLADIA = "gladia"
    ASSEMBLYAI = "assemblyai"
    GROQ = "groq"
    ELEVENLABS = "elevenlabs"


class FileType(str, Enum):
    TEXT = "text"
    JSON = "json"
    PDF = "pdf"
    MARKDOWN = "markdown"
    DOC = "doc"
    PPT = "ppt"
    EXCEL = "excel"
    HTML = "html"
    CSV = "csv"
    XML = "xml"
    CODE = "code"
    YAML = "yaml"

    AUDIO = "audio"

    IMAGE = "image"

    VIDEO = "video"


class TxtProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    rag_chunk_size_mb: Optional[int] = Field(default=Env.CHUNK_SIZE, description="The size of the RAG chunk in MB.")
    rag_chunk_overlap: Optional[int] = Field(default=Env.CHUNK_OVERLAP, description="The overlap of the RAG chunk.")
    tail_carry_chars: Optional[int] = Field(default=500, description="The number of characters to carry over to the next chunk.")


class CodeProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    language: Language = Field(..., description="The language of the document file.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    rag_chunk_size: Optional[int] = Field(default=Env.CHUNK_SIZE, description="The size of the RAG chunk.")
    rag_chunk_overlap: Optional[int] = Field(default=Env.CHUNK_OVERLAP, description="The overlap of the RAG chunk.")
    tail_carry_chars: Optional[int] = Field(default=500, description="The number of characters to carry over to the next chunk.")


class CSVProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    start_row: int = Field(..., description="The start row of the document file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    rows_per_io_buffer: int = Field(..., description="The number of rows to read from disk at once.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    group_size: Optional[int] = Field(default=10, description="The size of the RAG chunk.")
    max_group_size: Optional[int] = Field(default=20, description="The size of the RAG chunk.")


class DocxProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    pages_per_batch: Optional[float] = Field(default=20, description="The number of pages to read from disk at once.")
    rag_chunk_size: Optional[int] = Field(default=Env.CHUNK_SIZE, description="The size of the RAG chunk.")
    rag_chunk_overlap: Optional[int] = Field(default=Env.CHUNK_OVERLAP, description="The overlap of the RAG chunk.")
    tail_carry_chars: Optional[int] = Field(default=500, description="The number of characters to carry over to the next chunk.")


class ExcelProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    start_row: int = Field(..., description="The start row of the document file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    sheet: Optional[str | int] = Field(default=0, description="The sheet name or 0-based index (default: first sheet).")
    rows_per_io_buffer: int = Field(..., description="The number of rows to read from disk at once.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    group_size: Optional[int] = Field(default=10, description="The size of the RAG chunk.")
    max_group_size: Optional[int] = Field(default=20, description="The size of the RAG chunk.")


class HtmlProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    start_unit: int = Field(..., description="The start unit of the document file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    units_per_buffer: Optional[int] = Field(default=0, description="The number of units to read from disk at once.")
    rows_per_io_buffer: int = Field(..., description="The number of rows to read from disk at once.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    group_size: Optional[int] = Field(default=10, description="The size of the RAG chunk.")
    max_group_size: Optional[int] = Field(default=20, description="The size of the RAG chunk.")


class JsonProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    start_object: int = Field(..., description="The start object of the document file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    objects_per_buffer: Optional[int] = Field(default=500, description="The number of objects to read from disk at once.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    group_size: Optional[int] = Field(default=10, description="The size of the RAG chunk.")
    max_group_size: Optional[int] = Field(default=20, description="The size of the RAG chunk.")


class PdfProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    pages_per_batch: Optional[int] = Field(default=20, description="The number of pages to read from disk at once.")
    rag_chunk_size: Optional[int] = Field(default=Env.CHUNK_SIZE, description="The size of the RAG chunk.")
    rag_chunk_overlap: Optional[int] = Field(default=Env.CHUNK_OVERLAP, description="The overlap of the RAG chunk.")
    tail_carry_chars: Optional[int] = Field(default=500, description="The number of characters to carry over to the next chunk.")


class PptxProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    pages_per_batch: Optional[int] = Field(default=20, description="The number of pages to read from disk at once.")
    rag_chunk_size: Optional[int] = Field(default=Env.CHUNK_SIZE, description="The size of the RAG chunk.")
    rag_chunk_overlap: Optional[int] = Field(default=Env.CHUNK_OVERLAP, description="The overlap of the RAG chunk.")


class XmlProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    start_object: int = Field(..., description="The start object of the document file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    record_tag: Optional[str] = Field(default=None, description="The repeating element tag.")
    objects_per_buffer: Optional[int] = Field(default=500, description="The number of objects to read from disk at once.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    group_size: Optional[int] = Field(default=10, description="The size of the RAG chunk.")
    max_group_size: Optional[int] = Field(default=20, description="The size of the RAG chunk.")


class YamlProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    start_object: int = Field(..., description="The start object of the document file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    objects_per_buffer: Optional[int] = Field(default=500, description="The number of objects to read from disk at once.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    group_size: Optional[int] = Field(default=10, description="The size of the RAG chunk.")
    max_group_size: Optional[int] = Field(default=20, description="The size of the RAG chunk.")
    scan_lines: Optional[int] = Field(default=100, description="The number of lines to scan for structure.")


class ImageProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    processor: OCRProcessor = Field(..., description="The OCR service to use.")
    api_key: str = Field(..., description="The API key for the OCR service.")
    start_page: int = Field(..., description="The start page of the document file.")
    max_pages_per_chunk: int = Field(..., description="The maximum number of pages per chunk.")
    is_last_ocr_batch: bool = Field(..., description="True if this is the last chunk.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    timeout: float = Field(default=60 * 10, description="The timeout for the OCR service.")
    md_path: str | None = Field(default=None, description="The path to the markdown file.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")

    # Llamaparse config
    llama_tier: Optional[Literal["fast", "cost_effective", "agentic", "agentic_plus"]] = Field(default="agentic", description="The tier of the Llamaparse service.")
    llama_version: Optional[str] = Field(default="latest", description="The version of the Llamaparse service.")
    llama_poll_interval: Optional[float] = Field(default=2.0, description="The poll interval for the Llamaparse service.")

    kwargs: Optional[Dict[str, Any]] = Field(default={}, description="The kwargs for the OCR service.")


class AudioProcessParams(BaseModel):
    file_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    processor: AudioProcessor = Field(..., description="The OCR service to use.")
    api_key: str = Field(..., description="The API key for the OCR service.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")

    segment_duration_min: Optional[float] = Field(default=10, description="The duration of the audio segment in minutes.")

    max_time_per_rag_chunk_min: Optional[float] = Field(default=2.0, description="The maximum time per RAG chunk in minutes.")
    max_words_per_rag_chunk: Optional[int] = Field(default=300, description="The maximum words per RAG chunk.")

    # ElevenLabs config
    base_url: Optional[str] = Field(default="https://api.elevenlabs.io", description="The base URL for the ElevenLabs API.")
    ele_model_id: Optional[str] = Field(default="scribe_v2", description="The model ID for the ElevenLabs API.")
    tag_audio_events: Optional[bool] = Field(default=True, description="True if audio events should be added.")
    diarize: Optional[bool] = Field(default=True, description="True if diarization should be added.")

    # Deepgram config
    deepgram_model: Optional[str] = Field(default="nova-3", description="The model to use for transcription.")
    diarize: Optional[bool] = Field(default=True, description="True if diarization should be added.")
    smart_format: Optional[bool] = Field(default=True, description="True if smart formatting should be added.")
    detect_language: Optional[bool] = Field(default=True, description="True if language detection should be added.")

    # Assembly Config
    speaker_labels: Optional[bool] = Field(default=True, description="True if speaker labels should be added.")
    language_detection: Optional[bool] = Field(default=True, description="True if language detection should be added.")

    # Gladia Config
    gladia_model: Optional[str] = Field(default="solaria-3", description="The model to use for transcription.")
    diarization: Optional[bool] = Field(default=True, description="True if diarization should be added.")

    # Groq
    groq_model: Optional[str] = Field(default="whisper-large-v3", description="The model to use for transcription.")

    timeout: float = Field(default=60 * 10, description="The timeout for the OCR service.")
    kwargs: Optional[Dict[str, Any]] = Field(default={}, description="The kwargs for the OCR service.")


class CommonParams(BaseModel):
    org_id: str = Field(..., description="The organization id.")
    project_id: uuid.UUID = Field(..., description="The project uuid.")
    doc_id: uuid.UUID = Field(..., description="The document id.")
    file_type: FileType = Field(..., description="The file type of the document.")


class MarkdownProcessParams(BaseModel):
    markdown_path: str = Field(..., description="The path to the document file.")
    filename: str = Field(..., description="The name of the document file.")
    file_chunk_number: int = Field(..., description="The chunk number of the file.")
    rag_chunk_start_index: int = Field(..., description="The start index of the RAG chunk.")
    is_last: bool = Field(..., description="True if this is the last chunk.")
    is_ocr_part: bool = Field(default=False, description="True if this is the last chunk.")
    ocr_params: Optional[ImageProcessParams] = Field(default=None, description="The OCR params.")
    max_chunk_size_mb: Optional[float] = Field(default=30, description="The maximum size of a chunk in MB.")
    tokenizer: Optional[str] = Field(default="gpt2", description="The tokenizer to use.")
    cache_dir: Optional[str] = Field(default=None, description="The directory to cache chunks in.")


class ProcessParams(CommonParams):
    filename: str = Field(..., description="The filename of the document.")

    # Text
    txt_params: Optional[TxtProcessParams] = None
    json_params: Optional[JsonProcessParams] = None
    xml_params: Optional[XmlProcessParams] = None
    pdf_params: Optional[PdfProcessParams] = None
    md_params: Optional[MarkdownProcessParams] = None
    yaml_params: Optional[YamlProcessParams] = None
    docx_params: Optional[DocxProcessParams] = None
    excel_params: Optional[ExcelProcessParams] = None
    code_params: Optional[CodeProcessParams] = None
    ppt_params: Optional[PptxProcessParams] = None
    html_params: Optional[HtmlProcessParams] = None
    csv_params: Optional[CSVProcessParams] = None

    # Image
    image_params: Optional[ImageProcessParams] = None

    # Audio
    audio_params: Optional[AudioProcessParams] = None
