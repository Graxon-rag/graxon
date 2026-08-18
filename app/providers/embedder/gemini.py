from langchain_google_genai.embeddings import GoogleGenerativeAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr
from .base import BaseEmbedder
from typing import Optional
import asyncio
import re


class GeminiEmbedder(BaseEmbedder):
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-embedding-001",
        dimension: int = 1536,
        **kwargs,
    ):
        if not api_key:
            raise ValueError("Gemini API key is required")

        self._embedder = GoogleGenerativeAIEmbeddings(
            api_key=SecretStr(api_key),
            model=model,
            **kwargs,
        )
        self._dimension = dimension

    def _extract_retry_delay(self, error_str: str) -> float:
        """Extract retry delay from error message, or default to 60s for 429 errors."""
        # Check for 'retry in XXs' pattern
        match = re.search(r"retry in ([\d\.]+)s", error_str)
        if match:
            return float(match.group(1)) + 1.0  # Add 1s safety buffer

        # Check for 'retryDelay': 'XXs' pattern
        match = re.search(r"retryDelay':\s*'(\d+)s'", error_str)
        if match:
            return float(match.group(1)) + 1.0

        return 60.0  # Safe default cooldown for RPM resets

    async def aembed(self, text: str, **kwargs) -> list[float]:
        """Embed a single string with dynamic 429 rate limit backoff."""
        retry_count = 0
        max_retries = 3
        base_delay = 1

        while retry_count < max_retries:
            try:
                return await self._embedder.aembed_query(
                    text,
                    output_dimensionality=self._dimension,
                    **kwargs,
                )
            except Exception as e:
                retry_count += 1
                error_str = str(e)

                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    wait_time = self._extract_retry_delay(error_str)
                    logger.warning({
                        "message": f"Gemini Rate limit hit (429). Backing off for {wait_time:.1f}s",
                        "retry_count": retry_count,
                    })
                else:
                    wait_time = base_delay * (2 ** (retry_count - 1))

                if retry_count >= max_retries:
                    logger.error({
                        "message": "Max retries reached. Failed to embed text via Gemini.",
                        "error": error_str,
                    })
                    raise e

                await asyncio.sleep(wait_time)

        return []

    async def aembed_batch(
        self,
        texts: list[str],
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> list[list[float]]:
        """Embed a list of strings with dynamic 429 rate limit backoff."""
        if not texts:
            return []

        if batch_size and len(texts) > batch_size:
            results: list[list[float]] = []
            for i in range(0, len(texts), batch_size):
                chunk = texts[i: i + batch_size]
                chunk_embeddings = await self._embed_batch_with_retry(chunk, **kwargs)
                results.extend(chunk_embeddings)
            return results

        return await self._embed_batch_with_retry(texts, **kwargs)

    async def _embed_batch_with_retry(self, texts: list[str], **kwargs) -> list[list[float]]:
        retry_count = 0
        max_retries = 3
        base_delay = 1

        while retry_count < max_retries:
            try:
                return await self._embedder.aembed_documents(
                    texts,
                    output_dimensionality=self._dimension,
                    **kwargs,
                )
            except Exception as e:
                retry_count += 1
                error_str = str(e)

                if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                    wait_time = self._extract_retry_delay(error_str)
                    logger.warning({
                        "message": f"Gemini Batch Rate limit hit (429). Waiting {wait_time:.1f}s",
                        "retry_count": retry_count,
                        "batch_size": len(texts),
                    })
                else:
                    wait_time = base_delay * (2 ** (retry_count - 1))

                if retry_count >= max_retries:
                    logger.error({
                        "message": "Max retries reached. Failed to batch embed via Gemini.",
                        "error": error_str,
                    })
                    raise e

                await asyncio.sleep(wait_time)

        return []
