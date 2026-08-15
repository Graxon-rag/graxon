from datalab_sdk import AsyncDatalabClient
from .base import OCRProvider


class DatalabOCR(OCRProvider):
    def __init__(self, api_key: str, timeout: int = 60 * 10, **kwargs):
        self.api_key = api_key
        self._client = AsyncDatalabClient(api_key=api_key, timeout=timeout)

    async def client(self):
        return self._client
