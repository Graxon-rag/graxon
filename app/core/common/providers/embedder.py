from app.providers.embedder.embedder_factory import EmbedderFactory, BaseEmbedder
from ...schemas.project_config_schema import ProjectConfigDetailGetSchema


class EmbeddingProvider:
    @staticmethod
    def get(pc: ProjectConfigDetailGetSchema) -> BaseEmbedder:
        embedding_model = pc.embedding_model
        embedding_model_credential = pc.embedding_model_credential
        if embedding_model is None:
            raise Exception("embedding_model is None")
        if embedding_model_credential is None:
            raise Exception("embedding_model_credential is None")

        embedder = EmbedderFactory.embedder(embedding_model.provider, embedding_model_credential.api_key, embedding_model.model_id, embedding_model.dimension)

        return embedder
