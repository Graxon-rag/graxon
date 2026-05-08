class QDrantCollection:
    GRAXON_GEMINI = "graxon_gemini"
    GRAXON_OPENAI = "graxon_openai"
    GRAXON_VOYAGE = "graxon_voyage"


class QDrantGeminiConfig:
    collection_name = QDrantCollection.GRAXON_GEMINI
    dimension_1536 = 1536
    dimension_3072 = 3072
    gemini_1536 = "gemini_1536"
    gemini_3072 = "gemini_3072" 


class QDrantOpenAIConfig:
    collection_name = QDrantCollection.GRAXON_OPENAI
    dimension_1536 = 1536
    dimension_3072 = 3072
    openai_1536 = "openai_1536"
    openai_3072 = "openai_3072"


class QDrantVoyageConfig:
    collection_name = QDrantCollection.GRAXON_VOYAGE
    dimension_1024 = 1024
    dimension_2048 = 2048
    voyage_1024 = "voyage_1024"
    voyage_2048 = "voyage_2048"


QDrant_MODEL_MAP = {
    "gemini_1536": (QDrantCollection.GRAXON_GEMINI, QDrantGeminiConfig.gemini_1536),
    "gemini_3072": (QDrantCollection.GRAXON_GEMINI, QDrantGeminiConfig.gemini_3072),
    "openai_1536": (QDrantCollection.GRAXON_OPENAI, QDrantOpenAIConfig.openai_1536),
    "openai_3072": (QDrantCollection.GRAXON_OPENAI, QDrantOpenAIConfig.openai_3072),
    "voyage_1024": (QDrantCollection.GRAXON_VOYAGE, QDrantVoyageConfig.voyage_1024),
    "voyage_2048": (QDrantCollection.GRAXON_VOYAGE, QDrantVoyageConfig.voyage_2048),
}
