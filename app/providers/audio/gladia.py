from gladiaio_sdk import GladiaClient
from .base import BaseAudioProvider


class GladiaAudioProvider(BaseAudioProvider):
    def __init__(self, api_key: str, timeout: float = 60 * 10):
        self._client = GladiaClient(api_key=api_key, http_timeout=timeout).pre_recorded_async()

    async def client(self):
        return self._client
