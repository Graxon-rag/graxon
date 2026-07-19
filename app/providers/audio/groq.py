from .base import BaseAudioProvider
from groq import AsyncGroq


class GroqAudioProvider(BaseAudioProvider):
    def __init__(self, api_key: str):
        self._client = AsyncGroq(api_key=api_key)

    async def client(self):
        return self._client
