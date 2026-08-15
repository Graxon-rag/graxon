from llama_cloud.types.parsing_get_response import MarkdownPageMarkdownResultPage
from ...schemas.processor_schema import get_file_type, FileType
from app.providers.ocr.llamaparse import LlamaParseOCR
from .base import IMAGE_MIME_TYPES, OCRProcessor
from pypdf import PdfReader, PdfWriter
from app.utils.logger import logger
from typing import Tuple, Literal
from pathlib import Path
import mimetypes
import asyncio


LLAMA_TEMP_DIR = Path("temp/llamaparse")

TierType = Literal["fast", "cost_effective", "agentic", "agentic_plus"]


class LlamaCloudOCRProcessor(OCRProcessor):
    def __init__(
        self,
        file_path: str,
        filename: str,
        api_key: str,
        start_page: int = 0,
        max_pages_per_chunk: int = 100,
        tier: TierType = "agentic",
        version: str = "latest",
        poll_interval: float = 2.0,
        timeout: float = 60 * 10,
        **kwargs
    ):
        self.file_path = Path(file_path)
        self.filename = filename
        self.start_page = start_page
        self.max_pages_per_chunk = max_pages_per_chunk
        self.tier = tier
        self.version = version
        self.poll_interval = poll_interval
        self.timeout = timeout

        self._ocr = LlamaParseOCR(api_key=api_key, timeout=timeout, **kwargs)

        self._mime_type = (
            mimetypes.guess_type(str(self.file_path))[0] or "application/octet-stream"
        )
        self._is_image = self._mime_type in IMAGE_MIME_TYPES

        LLAMA_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def process(self) -> Tuple[Path, int, bool]:
        logger.info(f"Processing via LlamaCloud {self.filename}")

        file_type = get_file_type(self.filename)

        if self._is_image:
            return await self._process_image()
        if file_type == FileType.DOC or file_type == FileType.PPT:
            self.file_path = await self._convert_to_pdf(self.file_path)

        return await self._process_pdf()

    # -------------------------------------------------------------------------
    # Image — single-shot parse (no splitting)
    # -------------------------------------------------------------------------

    async def _process_image(self) -> Tuple[Path, int, bool]:
        markdown = await self._upload_and_parse(
            file_path=self.file_path,
            upload_filename=self.file_path.name,
            mime_type=self._mime_type,
        )

        md_path = self._save_markdown(
            markdown=markdown,
            stem=self.file_path.stem,
            suffix="",
        )

        return md_path, 0, True

    # -------------------------------------------------------------------------
    # PDF — physically split by page range, then upload just that slice
    # -------------------------------------------------------------------------

    async def _process_pdf(self) -> Tuple[Path, int, bool]:
        """
        Reads pages [start_page : start_page + max_pages_per_chunk], writes them
        out as a standalone temp PDF (like MistralOCRProcessor does), and uploads
        only that slice — instead of uploading the whole original file every batch
        and relying on target_pages server-side.
        """
        reader = PdfReader(str(self.file_path))
        total_pages = len(reader.pages)

        if self.start_page >= total_pages:
            raise ValueError(
                f"start_page={self.start_page} is out of range. "
                f"PDF has {total_pages} pages."
            )

        end_page = min(self.start_page + self.max_pages_per_chunk, total_pages)
        is_last = end_page >= total_pages

        writer = PdfWriter()
        for page_idx in range(self.start_page, end_page):
            writer.add_page(reader.pages[page_idx])

        pdf_path = self._save_pdf_chunk(writer, start=self.start_page, end=end_page)

        markdown = await self._upload_and_parse(
            file_path=pdf_path,
            upload_filename=pdf_path.name,
            mime_type="application/pdf",
        )

        md_path = self._save_markdown(
            markdown=markdown,
            stem=self.file_path.stem,
            suffix=f"_pages_{self.start_page}_{end_page - 1}",
        )

        return md_path, end_page, is_last

    # -------------------------------------------------------------------------
    # DOC/PPT — convert to PDF before OCR
    # -------------------------------------------------------------------------

    async def _convert_to_pdf(self, src: Path) -> Path:
        """
        Converts a .doc/.docx/.ppt/.pptx file to PDF via LibreOffice headless,
        writing the result into LLAMA_TEMP_DIR. Returns the converted path.
        """
        logger.info(f"Converting {src.name} to PDF via LibreOffice")

        proc = await asyncio.create_subprocess_exec(
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(LLAMA_TEMP_DIR), str(src),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"LibreOffice conversion failed for {src}: {stderr.decode(errors='ignore')}"
            )

        converted = LLAMA_TEMP_DIR / f"{src.stem}.pdf"
        if not converted.exists():
            raise RuntimeError(
                f"LibreOffice reported success but output PDF not found: {converted}"
            )

        return converted

    # -------------------------------------------------------------------------
    # LlamaCloud upload → parse → poll → extract markdown
    # -------------------------------------------------------------------------

    async def _upload_and_parse(
        self,
        file_path: Path,
        upload_filename: str,
        mime_type: str,
    ) -> str:
        """
        Uploads just this page-range slice (or the whole image) — no more
        target_pages/page_ranges param needed, since the file itself now only
        contains the pages we want parsed.
        """
        client = await self._ocr.client()

        logger.info(f"Uploading {upload_filename} to LlamaCloud")

        with open(file_path, "rb") as f:
            file_obj = await client.files.create(
                file=(upload_filename, f, mime_type),
                purpose="parse",
            )

        parse_kwargs = dict(
            file_id=file_obj.id,
            tier=self.tier,
            version=self.version,
            output_options={
                "markdown": {
                    "tables": {
                        "output_tables_as_markdown": True
                    }
                }
            },
            timeout=self.timeout,
        )

        logger.info(f"Creating LlamaCloud parse job with {parse_kwargs}")

        job = await client.parsing.create(**parse_kwargs)  # type: ignore

        logger.info(f"Created LlamaCloud parse job {job.id}")

        elapsed = 0.0
        while True:
            poll = await client.parsing.get(job.id)
            status = poll.job.status

            logger.info(f"Polling LlamaCloud parse job {job.id} with status={status}")

            if status == "COMPLETED":
                break
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(
                    f"LlamaCloud parse job {job.id} ended with status={status}. "
                    f"Error: {poll.job.error_message or 'no error message'}"
                )

            if elapsed >= self.timeout:
                raise TimeoutError(
                    f"LlamaCloud parse job {job.id} timed out after {self.timeout}s"
                )

            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval

        result = await client.parsing.get(job.id, expand=["markdown"])

        if result.markdown is None:
            raise RuntimeError(
                f"LlamaCloud job {job.id} completed but returned no markdown."
            )

        parts = []
        for page in result.markdown.pages:
            if not page.success:
                print(f"Warning: page {page.page_number} failed to parse, skipping.")
                continue
            if isinstance(page, MarkdownPageMarkdownResultPage):
                parts.append(page.markdown)

        return "\n\n".join(parts)

    # -------------------------------------------------------------------------
    # File helpers
    # -------------------------------------------------------------------------

    def _save_pdf_chunk(self, writer: PdfWriter, start: int, end: int) -> Path:
        """Writes the PDF slice to temp/llamaparse/{stem}_pages_{start}_{end-1}.pdf"""
        pdf_path = LLAMA_TEMP_DIR / f"{self.file_path.stem}_pages_{start}_{end - 1}.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)
        return pdf_path

    def _save_markdown(self, markdown: str, stem: str, suffix: str) -> Path:
        md_path = LLAMA_TEMP_DIR / f"{stem}{suffix}.md"
        md_path.write_text(markdown, encoding="utf-8")
        return md_path
