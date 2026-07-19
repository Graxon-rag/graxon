from deepgram import AsyncDeepgramClient
from .base import BaseAudioProvider


class DeepgramProvider(BaseAudioProvider):
    def __init__(self, api_key: str):
        self._client = AsyncDeepgramClient(api_key=api_key)

    async def client(self):
        return self._client
