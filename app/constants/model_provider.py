from enum import Enum


class LLMModelProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"


class EmbeddingModelProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    VOYAGE = "voyage"


class ModelProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    CLAUDE = "claude"
    VOYAGE = "voyage"
