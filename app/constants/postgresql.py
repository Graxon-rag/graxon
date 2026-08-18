class PGTables:
    ORGANIZATION_TABLE: str = "organizations"
    PROJECT_TABLE: str = "projects"
    PROJECT_CONFIG_TABLE: str = "project_configs"
    RERANKER_MODEL_TABLE: str = "reranker_models"
    SPARSE_TEXT_MODEL_TABLE: str = "sparse_text_models"
    MODEL_CREDENTIAL_TABLE: str = "model_credentials"
    LLM_MODEL_TABLE: str = "llm_models"
    EMBEDDING_MODEL_TABLE: str = "embedding_models"
    DOCUMENT_TABLE: str = "documents"
    OCR_MODEL_TABLE: str = "ocr_models"
    AUDIO_MODEL_TABLE: str = "audio_models"
    VIDEO_MODEL_TABLE: str = "video_models"
    WEBHOOK_TABLE: str = "webhooks"
    PROJECT_VARIABLES_TABLE = "project_variables"
    CHUNK_TABLE: str = "chunks"


class PGDatabase:
    GRAXON_DATABASE: str = "graxon"
