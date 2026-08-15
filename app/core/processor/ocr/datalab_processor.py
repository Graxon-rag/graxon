from ...schemas.processor_schema import get_file_type, FileType
from app.providers.ocr.datalabio import DatalabOCR
from .base import IMAGE_MIME_TYPES, OCRProcessor
from datalab_sdk.models import ConversionResult
from pypdf import PdfReader, PdfWriter
from app.utils.logger import logger
from typing import Tuple
from pathlib import Path
import mimetypes
import asyncio


# Where all temp files live
DATALAB_TEMP_DIR = Path("temp/datalab")


class DatalabOCRProcessor(OCRProcessor):
    def __init__(
        self,
        file_path: str,
        filename: str,
        api_key: str,
        start_page: int = 0,               # 0-based page index (PDF only, ignored for images)
        max_pages_per_chunk: int = 100,    # max pages per convert() call
        max_chunk_size_mb: float = 30,     # stop before exceeding this per chunk
        timeout: int = 60 * 10,            # seconds (datalab uses seconds, not ms)
        **kwargs
    ):
        self.file_path = Path(file_path)
        self.filename = filename
        self.start_page = start_page
        self.max_pages_per_chunk = max_pages_per_chunk
        self.max_chunk_size_bytes = int(max_chunk_size_mb * 1024 * 1024)
        self.timeout = timeout

        self._ocr = DatalabOCR(api_key=api_key, timeout=timeout, **kwargs)

        self._mime_type = mimetypes.guess_type(str(self.file_path))[0] or "application/octet-stream"
        self._is_image = self._mime_type in IMAGE_MIME_TYPES

        DATALAB_TEMP_DIR.mkdir(parents=True, exist_ok=True)

    async def process(self) -> Tuple[Path, int, bool]:
        """
        Single image → convert whole file at once → save markdown → return path.
        PDF         → split pages start_page : start_page + max_pages_per_chunk
                      (capped at max_chunk_size_mb) → convert → save markdown.

        Returns:
            md_path:    Path to saved .md file in temp/
                        → pass directly to MarkdownProcessor
            next_page:  pass as start_page to next queue message (PDF only, 0 for images)
            is_last:    True = no more pages remain
        """
        logger.info(f"Processing via Datalab {self.filename}")

        file_type = get_file_type(self.filename)

        if self._is_image:
            return await self._process_image()
        if file_type == FileType.DOC or file_type == FileType.PPT:
            self.file_path = await self._convert_to_pdf(self.file_path)

        return await self._process_pdf()

    # -------------------------------------------------------------------------
    # Image — single shot, no splitting needed
    # -------------------------------------------------------------------------

    async def _process_image(self) -> Tuple[Path, int, bool]:
        """
        Passes the image directly to datalab convert().
        Always returns is_last=True — images have no pages to paginate.
        """
        markdown = await self._convert(str(self.file_path))

        md_path = self._save_markdown(
            markdown=markdown,
            stem=self.file_path.stem,
            suffix="",
        )

        return md_path, 0, True

    # -------------------------------------------------------------------------
    # PDF — split by page range + size cap, then convert
    # -------------------------------------------------------------------------

    async def _process_pdf(self) -> Tuple[Path, int, bool]:
        """
        Splits the PDF into a page-range slice respecting both:
          - max_pages_per_chunk (count guard)
          - max_chunk_size_mb   (size guard — stops before the page that would breach it)

        Saves the slice as temp/{stem}_pages_{start}_{end}.pdf,
        converts it via datalab, saves markdown as temp/{stem}_pages_{start}_{end}.md.
        """
        reader = PdfReader(str(self.file_path))
        total_pages = len(reader.pages)

        if self.start_page >= total_pages:
            raise ValueError(
                f"start_page={self.start_page} is out of range. "
                f"PDF has {total_pages} pages."
            )

        # Build page-range slice with dual guard
        writer = PdfWriter()
        accumulated_bytes = 0
        end_page = self.start_page

        for page_idx in range(self.start_page, total_pages):
            page = reader.pages[page_idx]

            # Estimate this page's size before adding it
            page_bytes = self._estimate_page_size(page)

            # Size guard — stop before adding a page that would breach the cap
            if accumulated_bytes + page_bytes > self.max_chunk_size_bytes and writer.pages:
                break

            writer.add_page(page)
            accumulated_bytes += page_bytes
            end_page = page_idx + 1  # exclusive end

            # Page count guard
            if (end_page - self.start_page) >= self.max_pages_per_chunk:
                break

        is_last = end_page >= total_pages

        # Save the PDF slice to temp/datalab
        pdf_path = self._save_pdf_chunk(writer, start=self.start_page, end=end_page)

        # Convert via datalab SDK
        markdown = await self._convert(str(pdf_path))

        # Save markdown to temp/datalab
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
        writing the result into DATALAB_TEMP_DIR. Returns the converted path.
        """
        logger.info(f"Converting {src.name} to PDF via LibreOffice")

        proc = await asyncio.create_subprocess_exec(
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(DATALAB_TEMP_DIR), str(src),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(
                f"LibreOffice conversion failed for {src}: {stderr.decode(errors='ignore')}"
            )

        converted = DATALAB_TEMP_DIR / f"{src.stem}.pdf"
        if not converted.exists():
            raise RuntimeError(
                f"LibreOffice reported success but output PDF not found: {converted}"
            )

        return converted

    # -------------------------------------------------------------------------
    # Datalab convert — handles both result types from the SDK
    # -------------------------------------------------------------------------

    async def _convert(self, file_path: str) -> str:
        """
        Calls datalab client.convert() and normalises both return types:

          ConversionResult with .markdown  → return markdown string directly
          ConversionResult with .output_path → read the file and return its text

        Mirrors your reference code exactly.
        """
        client = await self._ocr.client()
        result = await client.convert(file_path)

        if result.error:
            raise RuntimeError(f"Datalab conversion failed: {result.error}")

        if isinstance(result, ConversionResult):
            if result.markdown is not None:
                # SDK returned markdown directly
                return result.markdown
            else:
                raise RuntimeError("Datalab SDK returned ConversionResult with empty markdown.")
        else:
            # SDK returned a file path to the generated markdown
            output_path = Path(result.output_path)
            return output_path.read_text(encoding="utf-8")

    # -------------------------------------------------------------------------
    # File helpers
    # -------------------------------------------------------------------------

    def _estimate_page_size(self, page) -> int:
        """Estimate byte size of a single PDF page via in-memory write."""
        import io
        probe = PdfWriter()
        probe.add_page(page)
        buf = io.BytesIO()
        probe.write(buf)
        return buf.tell()

    def _save_pdf_chunk(self, writer: PdfWriter, start: int, end: int) -> Path:
        """
        Writes the PDF slice to temp/{stem}_pages_{start}_{end-1}.pdf
        Kept in temp even after conversion (same behaviour as OCRProcessor).
        """
        pdf_path = DATALAB_TEMP_DIR / f"{self.file_path.stem}_pages_{start}_{end - 1}.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)
        return pdf_path

    def _save_markdown(self, markdown: str, stem: str, suffix: str) -> Path:
        """Writes markdown to temp/{stem}{suffix}.md and returns the path."""
        md_path = DATALAB_TEMP_DIR / f"{stem}{suffix}.md"
        md_path.write_text(markdown, encoding="utf-8")
        return md_path
