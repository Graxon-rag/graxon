from langchain_voyageai import VoyageAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr
from typing import Literal
from .base import BaseEmbedder
import asyncio

VoyageDimension = Literal[256, 512, 1024, 2048]


class VoyageEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model: str = "voyage-4-lite", dimension: VoyageDimension = 1024, **kwargs):
        if not api_key:
            raise ValueError("Voyage API key is required")

        if dimension not in (1024, 2048):
            raise ValueError("Invalid Voyage dimension only supports 1024 and 2048")

        self._embedder = VoyageAIEmbeddings(api_key=SecretStr(api_key), model=model, output_dimension=dimension, **kwargs)

    async def aembed(self, text: str, **kwargs) -> list[float]:
        retry_count = 0
        max_retries = 3
        base_delay = 1  # Starting delay in seconds

        while retry_count < max_retries:
            try:
                return await self._embedder.aembed_query(text, **kwargs)

            except Exception as e:
                retry_count += 1
                logger.warning({
                    "message": f"Embedding attempt {retry_count} failed",
                    "error": str(e),
                    "text_snippet": text[:50]
                })

                if retry_count >= max_retries:
                    logger.error({"message": "Max retries reached. Failed to embed text via Gemini.", "error": str(e)})
                    raise e

                # Exponential backoff: 1s, 2s, 4s...
                await asyncio.sleep(base_delay * (2 ** (retry_count - 1)))

        return []
