from abc import ABC, abstractmethod
from typing import Tuple
from pathlib import Path


# Image MIME types treated as single-shot (no splitting)
IMAGE_MIME_TYPES = {
    "image/png", "image/jpeg", "image/jpg", "image/webp",
    "image/tiff", "image/bmp", "image/gif",
}


class OCRProcessor(ABC):

    @abstractmethod
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

        raise NotImplementedError
