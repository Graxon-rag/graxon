from langchain_openai.embeddings import OpenAIEmbeddings
from app.utils.logger import logger
from pydantic import SecretStr
from .base import BaseEmbedder
from typing import Optional
import asyncio


class OpenaiEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model: str = "text-embedding-3-large", **kwargs):
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self._embedder = OpenAIEmbeddings(api_key=SecretStr(api_key), model=model, **kwargs)

    async def aembed(self, text: str, **kwargs) -> list[float]:
        """Embed a single string."""
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
                    "text_snippet": text[:50],
                })

                if retry_count >= max_retries:
                    logger.error({
                        "message": "Max retries reached. Failed to embed text via OpenAI.",
                        "error": str(e),
                    })
                    raise e

                # Exponential backoff: 1s, 2s, 4s...
                await asyncio.sleep(base_delay * (2 ** (retry_count - 1)))

        return []

    async def aembed_batch(
        self,
        texts: list[str],
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> list[list[float]]:
        """Embed a list of strings with retry logic and optional client-side batching."""
        if not texts:
            return []

        # If a batch size is specified, chunk the input list
        if batch_size and len(texts) > batch_size:
            results: list[list[float]] = []
            for i in range(0, len(texts), batch_size):
                chunk = texts[i: i + batch_size]
                chunk_embeddings = await self._embed_batch_with_retry(chunk, **kwargs)
                results.extend(chunk_embeddings)
            return results

        return await self._embed_batch_with_retry(texts, **kwargs)

    async def _embed_batch_with_retry(self, texts: list[str], **kwargs) -> list[list[float]]:
        """Internal helper for executing a single batch with exponential backoff."""
        retry_count = 0
        max_retries = 3
        base_delay = 1

        while retry_count < max_retries:
            try:
                return await self._embedder.aembed_documents(texts, **kwargs)

            except Exception as e:
                retry_count += 1
                logger.warning({
                    "message": f"Batch embedding attempt {retry_count} failed",
                    "error": str(e),
                    "batch_size": len(texts),
                    "first_item_snippet": texts[0][:50] if texts else "",
                })

                if retry_count >= max_retries:
                    logger.error({
                        "message": "Max retries reached. Failed to batch embed texts via OpenAI.",
                        "error": str(e),
                    })
                    raise e

                await asyncio.sleep(base_delay * (2 ** (retry_count - 1)))

        return []
