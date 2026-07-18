from mistralai.client import Mistral
from .base import OCRProvider


class MistralOCR(OCRProvider):
    def __init__(self, api_key: str, timeout: int = 60 * 10, **kwargs):
        self.api_key = api_key
        self._client = Mistral(api_key=api_key, timeout_ms=timeout * 1000, **kwargs)

    async def client(self):
        return self._client
