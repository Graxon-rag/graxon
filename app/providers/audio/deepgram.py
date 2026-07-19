from deepgram import AsyncDeepgramClient
from .base import BaseAudioProvider


class DeepgramProvider(BaseAudioProvider):
    def __init__(self, api_key: str, timeout: float = 60 * 10):
        self._client = AsyncDeepgramClient(api_key=api_key, timeout=timeout)

    async def client(self):
        return self._client
