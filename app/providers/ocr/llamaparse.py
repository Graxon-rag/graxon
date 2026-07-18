from llama_cloud import AsyncLlamaCloud
from .base import OCRProvider


class LlamaParseOCR(OCRProvider):
    def __init__(self, api_key: str, timeout: float = 60 * 10, **kwargs):
        self.api_key = api_key
        self._client = AsyncLlamaCloud(api_key=api_key, timeout=timeout, **kwargs)

    async def client(self):
        return self._client
