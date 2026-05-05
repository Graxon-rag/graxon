from app.constants.model_provider import LLMModelProvider, EmbeddingModelProvider


class ModelProviderHelper:

    @staticmethod
    def get_llm_model_provider(provider_name: str) -> LLMModelProvider:
        if provider_name == LLMModelProvider.OPENAI.value:
            return LLMModelProvider.OPENAI
        elif provider_name == LLMModelProvider.DEEPSEEK.value:
            return LLMModelProvider.DEEPSEEK
        elif provider_name == LLMModelProvider.CLAUDE.value:
            return LLMModelProvider.CLAUDE
        elif provider_name == LLMModelProvider.GEMINI.value:
            return LLMModelProvider.GEMINI
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    @staticmethod
    def get_embedding_model_provider(provider_name: str) -> EmbeddingModelProvider:
        if provider_name == EmbeddingModelProvider.OPENAI.value:
            return EmbeddingModelProvider.OPENAI
        elif provider_name == EmbeddingModelProvider.GEMINI.value:
            return EmbeddingModelProvider.GEMINI
        elif provider_name == EmbeddingModelProvider.VOYAGE.value:
            return EmbeddingModelProvider.VOYAGE
        else:
            raise ValueError(f"Unknown Embedding provider: {provider_name}")
