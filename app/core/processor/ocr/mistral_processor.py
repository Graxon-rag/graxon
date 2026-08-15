from ...schemas.processor_schema import get_file_type, FileType
from app.providers.ocr.mistral import MistralOCR
from .base import IMAGE_MIME_TYPES, OCRProcessor
from mistralai.client.models import File
from pypdf import PdfReader, PdfWriter
from app.utils.logger import logger
from typing import Tuple
from pathlib import Path
import mimetypes
import asyncio


# Where all temp files live
MISTRAL_TEMP_DIR = Path("temp/mistral")


class MistralOCRProcessor(OCRProcessor):
    def __init__(
        self,
        file_path: str,
        filename: str,
        api_key: str,
        start_page: int = 0,               # 0-based page index (PDF only, ignored for images)
        max_pages_per_chunk: int = 100,    # Mistral recommended max per call
        max_chunk_size_mb: float = 30,     # Mistral hard limit is 50MB — stay safe at 30
        timeout: int = 60 * 10,  # 10 minutes
        **kwargs
    ):
        self.file_path = Path(file_path)
        self.filename = filename
        self.start_page = start_page
        self.max_pages_per_chunk = max_pages_per_chunk
        self.max_chunk_size_bytes = int(max_chunk_size_mb * 1024 * 1024)

        self._mime_type = mimetypes.guess_type(str(self.file_path))[0] or "application/octet-stream"
        self._is_image = self._mime_type in IMAGE_MIME_TYPES

        self.timeout_ms = timeout * 1000
        self._ocr = MistralOCR(api_key=api_key, timeout=timeout, **kwargs)
        self.ocr_model = kwargs.get("model", "mistral-ocr-latest")

        # Ensure temp dir exists
        MISTRAL_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    async def process(self) -> Tuple[Path, int, bool]:
        """
        Single image → OCR the whole file at once.
        PDF         → Split pages start_page : start_page + max_pages_per_chunk
                      (capped at max_chunk_size_mb), upload, OCR.

        Returns:
            md_path:        Path to the saved markdown file in temp/
                            → pass directly to MarkdownProcessor
            next_page:      pass as start_page to the next queue message (PDF only)
                            → always 0 for images (single shot)
            is_last:        True = no more pages remain, this was the final batch
        """
        logger.info(f"Processing via Mistral {self.filename}")
        file_type = get_file_type(self.filename)

        if self._is_image:
            return await self._process_image()
        if file_type == FileType.DOC or file_type == FileType.PPT:
            self.file_path = await self._convert_to_pdf(self.file_path)

        return await self._process_pdf()

    # -------------------------------------------------------------------------
    # DOC/PPT — convert to PDF before OCR
    # -------------------------------------------------------------------------

    async def _convert_to_pdf(self, src: Path) -> Path:
        """
        Converts a .doc/.docx/.ppt/.pptx file to PDF via LibreOffice headless,
        writing the result into MISTRAL_TEMP_DIR. Returns the converted path.
        """
        logger.info(f"Converting {src.name} to PDF via LibreOffice")

        proc = await asyncio.create_subprocess_exec(
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(MISTRAL_TEMP_DIR), str(src),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"LibreOffice conversion failed for {src}: {stderr.decode(errors='ignore')}"
            )

        converted = MISTRAL_TEMP_DIR / f"{src.stem}.pdf"
        if not converted.exists():
            raise RuntimeError(
                f"LibreOffice reported success but output PDF not found: {converted}"
            )

        return converted

    # -------------------------------------------------------------------------
    # Image — process entire file in one shot
    # -------------------------------------------------------------------------

    async def _process_image(self) -> Tuple[Path, int, bool]:
        """
        Images have no pages to split — upload and OCR the whole file.
        Always returns is_last=True.
        """
        file_bytes = self.file_path.read_bytes()

        markdown = await self._upload_and_ocr(
            file_bytes=file_bytes,
            upload_filename=self.file_path.name,
            mime_type=self._mime_type,
        )

        md_path = self._save_markdown(
            markdown=markdown,
            stem=self.file_path.stem,
            suffix="",           # no chunk suffix for single image
        )

        return md_path, 0, True

    # -------------------------------------------------------------------------
    # PDF — split by page range + size cap, then OCR
    # -------------------------------------------------------------------------

    async def _process_pdf(self) -> Tuple[Path, int, bool]:
        """
        Reads the PDF, extracts pages start_page → start_page + max_pages_per_chunk
        (stops earlier if accumulated size exceeds max_chunk_size_mb).

        Saves the page-range slice as a temp PDF, uploads it, runs OCR,
        saves the resulting markdown, and returns the path + next_page + is_last.
        """
        reader = PdfReader(str(self.file_path))
        total_pages = len(reader.pages)

        if self.start_page >= total_pages:
            raise ValueError(
                f"start_page={self.start_page} is out of range. "
                f"PDF has {total_pages} pages."
            )

        # Build the page-range slice respecting both count and size caps
        writer = PdfWriter()
        accumulated_bytes = 0
        end_page = self.start_page  # exclusive end index — incremented below

        for page_idx in range(self.start_page, total_pages):
            page = reader.pages[page_idx]

            # Estimate page size by writing it alone to a temp buffer
            probe = PdfWriter()
            probe.add_page(page)
            page_bytes = self._estimate_writer_size(probe)

            # Size cap — stop before adding this page
            if accumulated_bytes + page_bytes > self.max_chunk_size_bytes and writer.pages:
                break

            writer.add_page(page)
            accumulated_bytes += page_bytes
            end_page = page_idx + 1  # exclusive

            # Page count cap
            if (end_page - self.start_page) >= self.max_pages_per_chunk:
                break

        is_last = end_page >= total_pages

        # Save the PDF slice to temp/mistral
        pdf_path = self._save_pdf_chunk(writer, start=self.start_page, end=end_page)

        # Upload and OCR the slice
        file_bytes = pdf_path.read_bytes()
        markdown = await self._upload_and_ocr(
            file_bytes=file_bytes,
            upload_filename=pdf_path.name,
            mime_type="application/pdf",
        )

        # Save markdown to temp/mistral
        md_path = self._save_markdown(
            markdown=markdown,
            stem=self.file_path.stem,
            suffix=f"_pages_{self.start_page}_{end_page - 1}",
        )

        return md_path, end_page, is_last

    # -------------------------------------------------------------------------
    # Mistral upload + OCR
    # -------------------------------------------------------------------------

    async def _upload_and_ocr(
        self,
        file_bytes: bytes,
        upload_filename: str,
        mime_type: str,
    ) -> str:
        """
        Uploads file_bytes to Mistral Files API, runs OCR,
        returns the full markdown string (all pages joined).
        """
        logger.info(f"Uploading {upload_filename} to Mistral")

        client = await self._ocr.client()
        uploaded = await client.files.upload_async(
            file=File(
                file_name=upload_filename,
                content=file_bytes,
                content_type=mime_type,
            ),
            purpose="ocr",
            timeout_ms=self.timeout_ms,
        )

        logger.info(f"Running Mistral OCR on {uploaded.id}")

        result = await client.ocr.process_async(
            model=self.ocr_model or "mistral-ocr-latest",
            timeout_ms=self.timeout_ms,
            document={
                "type": "file",
                "file_id": uploaded.id,
            },
        )

        # Join markdown from all pages with double newline separator
        return "\n\n".join(page.markdown for page in result.pages)

    # -------------------------------------------------------------------------
    # File helpers
    # -------------------------------------------------------------------------

    def _estimate_writer_size(self, writer: PdfWriter) -> int:
        """Estimate byte size of a PdfWriter by writing to an in-memory buffer."""
        import io
        buf = io.BytesIO()
        writer.write(buf)
        return buf.tell()

    def _save_pdf_chunk(self, writer: PdfWriter, start: int, end: int) -> Path:
        """
        Writes the PDF slice to temp/{stem}_pages_{start}_{end-1}.pdf
        Returns the path.
        """
        pdf_path = MISTRAL_TEMP_DIR / f"{self.file_path.stem}_pages_{start}_{end - 1}.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)
        return pdf_path

    def _save_markdown(self, markdown: str, stem: str, suffix: str) -> Path:
        """
        Writes markdown to temp/{stem}{suffix}.md
        Returns the path.
        """
        md_path = MISTRAL_TEMP_DIR / f"{stem}{suffix}.md"
        md_path.write_text(markdown, encoding="utf-8")
        return md_path
