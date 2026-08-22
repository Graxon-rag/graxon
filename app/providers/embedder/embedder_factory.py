from app.constants.model_provider import EmbeddingModelProvider
from .voyage import VoyageEmbedder, VoyageDimension
from .gemini import GeminiEmbedder
from .openai import OpenaiEmbedder
from .base import BaseEmbedder


class EmbedderFactory:

    @staticmethod
    def embedder(
        provider: EmbeddingModelProvider,
        api_key: str,
        model: str,
        dimension: int | VoyageDimension,
        **kwargs,
    ) -> BaseEmbedder:

        if provider == EmbeddingModelProvider.OPENAI:
            return OpenaiEmbedder(
                api_key=api_key,
                model=model,
                dimension=dimension,
                **kwargs,
            )

        elif provider == EmbeddingModelProvider.GEMINI:
            return GeminiEmbedder(
                api_key=api_key,
                model=model,
                dimension=dimension,
                **kwargs,
            )

        elif provider == EmbeddingModelProvider.VOYAGE:
            if dimension not in (256, 512, 1024, 2048):
                raise ValueError(
                    f"Invalid Voyage dimension: {dimension}. "
                    "Expected one of: 256, 512, 1024, 2048."
                )

            return VoyageEmbedder(
                api_key=api_key,
                model=model,
                dimension=dimension,
                **kwargs,
            )

        else:
            raise ValueError(f"Unknown Embedding provider: {provider}")
