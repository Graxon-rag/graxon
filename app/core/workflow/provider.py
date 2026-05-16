from app.constants.model_provider import LLMModelProvider, EmbeddingModelProvider
from app.providers.sparse_embedder.fast_embed import FastEmbedSparseEmbedder
from app.providers.fast_embedder.fast_embedder import FastEmbedEmbedder
from app.providers.fast_embedder.base import BaseFastEmbedEmbedder
from app.providers.sparse_embedder.base import BaseSparseEmbedder
from app.providers.reranker.fast_embed import FastEmbedReranker
from app.providers.embedder.openai import OpenaiEmbedder
from app.providers.embedder.gemini import GeminiEmbedder
from app.providers.embedder.voyage import VoyageEmbedder
from app.providers.embedder.base import BaseEmbedder
from app.providers.reranker.base import BaseReranker
from app.providers.llm.deepseek import DeepseekLLM
from app.providers.llm.openai import OpenaiLLM
from app.providers.llm.claude import ClaudeLLM
from app.providers.llm.gemini import GeminiLLM
from app.providers.llm.base import BaseLLM
from typing import Any, Optional


class WorkflowLLM:

    @staticmethod
    def llm(provider: LLMModelProvider, api_key: str, model: str, timeout: float = 60, stop: Any = None, **kwargs) -> BaseLLM:

        if provider == LLMModelProvider.OPENAI:
            return OpenaiLLM(api_key=api_key, model=model, timeout=timeout, **kwargs)
        elif provider == LLMModelProvider.DEEPSEEK:
            return DeepseekLLM(api_key=api_key, model=model, timeout=timeout, **kwargs)
        elif provider == LLMModelProvider.CLAUDE:
            return ClaudeLLM(api_key=api_key, model=model, timeout=timeout, stop=stop, **kwargs)
        elif provider == LLMModelProvider.GEMINI:
            return GeminiLLM(api_key=api_key, model=model, timeout=timeout, **kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")


class WorkflowEmbedder:

    @staticmethod
    def embedder(provider: EmbeddingModelProvider, api_key: str, model: str, dimension: int, **kwargs) -> BaseEmbedder:
        if provider == EmbeddingModelProvider.OPENAI:
            return OpenaiEmbedder(api_key=api_key, model=model, dimension=dimension, **kwargs)
        elif provider == EmbeddingModelProvider.GEMINI:
            return GeminiEmbedder(api_key=api_key, model=model, dimension=dimension, **kwargs)
        elif provider == EmbeddingModelProvider.VOYAGE:
            if dimension not in (1024, 2048):
                raise ValueError("Invalid Voyage dimension only supports 1024 and 2048")
            return VoyageEmbedder(api_key=api_key, model=model, dimension=dimension, **kwargs)
        else:
            raise ValueError(f"Unknown Embedding provider: {provider}")


class WorkflowReranker:

    @staticmethod
    def reranker(model: str, provider: Optional[str], **kwargs) -> BaseReranker:
        return FastEmbedReranker(rerank_model=model, **kwargs)


class WorkflowSparseEmbedder:

    @staticmethod
    def sparse_embedder(model: str, provider: Optional[str], **kwargs) -> BaseSparseEmbedder:
        return FastEmbedSparseEmbedder(embed_model=model, **kwargs)


class WorkflowFastEmbedder:

    @staticmethod
    def fast_embedder(model: str = "nomic-ai/nomic-embed-text-v1", provider: Optional[str] = None, **kwargs) -> BaseFastEmbedEmbedder:
        return FastEmbedEmbedder(model="nomic-ai/nomic-embed-text-v1", **kwargs)
