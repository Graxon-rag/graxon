from elevenlabs.client import AsyncElevenLabs
from .base import BaseAudioProvider


class ElevenlabsAudioProvider(BaseAudioProvider):
    def __init__(self, api_key: str):
        self._client = AsyncElevenLabs(api_key=api_key)

    async def client(self):
        return self._client
