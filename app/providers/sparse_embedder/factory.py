from app.core.schemas.sparse_text_model_schema import SparseModelProviderType, SparseModelProvider
from .pinecone_sparse_embedder import PineconeSparseEmbedder
from .fast_embed import FastEmbedSparseEmbedder
from .base import BaseSparseEmbedder


class SparseEmbedderFactory:

    @staticmethod
    def sparse_embedder(model: str, provider: SparseModelProvider, provider_type: SparseModelProviderType, api_key: str | None, **kwargs) -> BaseSparseEmbedder:
        if provider_type == SparseModelProviderType.CLOUD:
            if api_key is None:
                raise ValueError("For cloud provider, API key is required")
            if provider == SparseModelProvider.PINECONE:
                return PineconeSparseEmbedder(api_key=api_key, model=model, **kwargs)
            else:
                raise ValueError(f"Unknown Sparse Embedding provider: {provider}")
        else:
            return FastEmbedSparseEmbedder(model=model, **kwargs)
