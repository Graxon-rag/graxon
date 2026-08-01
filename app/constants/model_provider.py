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


class OCRModelProvider(str, Enum):
    DATALAB = "datalab"
    MISTRAL = "mistral"
    LLAMAPARSE = "llamaparse"


class AudioModelProvider(str, Enum):
    DEEPGRAM = "deepgram"
    GLADIA = "gladia"
    ASSEMBLYAI = "assemblyai"
    GROQ = "groq"
    ELEVENLABS = "elevenlabs"


class VideoModelProvider(str, Enum):
    TWELVELABS = "twelvelabs"
    GEMINI = "gemini"


class RerankerModelProvider(str, Enum):
    XENOVA = "xenova"
    BBAI = "baai"
    JINA = "jina"
    COHERE = "cohere"
    VOYAGE = "voyage"


class ModelProvider(str, Enum):
    # LLM
    DEEPSEEK = "deepseek"

    # Embedding
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    VOYAGE = "voyage"

    # OCR
    DATALAB = "datalab"
    MISTRAL = "mistral"
    LLAMAPARSE = "llamaparse"

    # Audio
    DEEPGRAM = "deepgram"
    GLADIA = "gladia"
    ASSEMBLYAI = "assemblyai"
    GROQ = "groq"
    ELEVENLABS = "elevenlabs"

    # Video
    TWELVELABS = "twelvelabs"

    # Reranker
    XENOVA = "xenova"
    BBAI = "baai"
    JINA = "jina"
    COHERE = "cohere"
