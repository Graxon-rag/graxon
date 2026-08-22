from app.providers.sparse_embedder.factory import SparseEmbedderFactory, BaseSparseEmbedder
from ...schemas.project_config_schema import ProjectConfigDetailGetSchema
from app.utils.logger import logger


class SparseEmbedderProvider:
    @staticmethod
    def get(pc: ProjectConfigDetailGetSchema) -> BaseSparseEmbedder | None:
        if not pc.sparse_embedding_enable:
            logger.warning("Sparse embedding is not enabled")
            return None
        sparse_embedding_model = pc.sparse_text_model
        sparse_embedding_model_credential = pc.sparse_text_model_credential
        if sparse_embedding_model is None:
            raise Exception("sparse_embedding is None")
        if sparse_embedding_model_credential is None:
            raise Exception("sparse_embedding_model_credential is None")

        if sparse_embedding_model.provider_type == "cloud" and sparse_embedding_model_credential is None:
            logger.error({"message": "Sparse Embedding Model Credential is not configured"})
            raise ValueError("Sparse Embedding Model Credential is not configured")

        sparse_provider = sparse_embedding_model.provider
        sparse_model = sparse_embedding_model.model_id
        api_key: str | None = sparse_embedding_model_credential and sparse_embedding_model_credential.api_key

        sparse_embedder = SparseEmbedderFactory.sparse_embedder(model=sparse_model, provider=sparse_provider, provider_type=sparse_embedding_model.provider_type, api_key=api_key)

        return sparse_embedder
