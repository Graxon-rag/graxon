from elevenlabs.client import AsyncElevenLabs
from .base import BaseAudioProvider


class ElevenlabsAudioProvider(BaseAudioProvider):
    def __init__(self, api_key: str, timeout: float = 60 * 10, base_url: str = "https://api.elevenlabs.io"):
        self._client = AsyncElevenLabs(api_key=api_key, timeout=timeout, base_url=base_url)

    async def client(self):
        return self._client
