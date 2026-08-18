
class EmbeddingLib:

    @staticmethod
    def get_model_key(provider: str, dimension: int) -> str:
        return f"{provider}_{dimension}"
