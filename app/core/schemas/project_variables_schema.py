from pydantic import BaseModel, Field


class ProjectVariableBase(BaseModel):
    # External Call / Batching
    embedding_chunk_batch_size: int = Field(
        default=30,
        ge=1,
        description="Number of text chunks processed in a single batch during dense embedding generation."
    )
    sparse_chunk_batch_size: int = Field(
        default=30,
        ge=1,
        description="Number of text chunks processed in a single batch during sparse embedding generation."
    )
    llm_tag_extraction_batch_size: int = Field(
        default=10,
        ge=1,
        description="Number of chunks sent per batch to the LLM for entity and tag extraction."
    )
    delay_between_chunk_processing_seconds: int = Field(
        default=10,
        ge=0,
        description="Cooldown delay (in seconds) between chunk processing batches to prevent API rate limiting."
    )

    # Chunks & Processing Limits
    chunk_size: int = Field(
        default=1500,
        gt=0,
        description="Target character count per document chunk."
    )
    chunk_overlap: int = Field(
        default=200,
        ge=0,
        description="Number of overlapping characters between consecutive chunks to maintain context."
    )
    max_chunks: int = Field(
        default=10000,
        gt=0,
        description="Maximum number of total chunks allowed for a single document or ingestion run."
    )
    max_chunk_size_mb: float = Field(
        default=4.0,
        gt=0.0,
        description="Maximum allowed size per chunk in megabytes (MB)."
    )
    max_pages_per_batch: int = Field(
        default=10,
        gt=0,
        description="Number of document pages parsed per batch during ingestion."
    )
    tail_carry_chars: int = Field(
        default=500,
        ge=0,
        description="Number of trailing characters carried over across page boundaries to avoid mid-sentence splits."
    )
    group_size_for_rag_chunk: int = Field(
        default=3,
        ge=1,
        description="Default number of neighboring chunks grouped together to form a contextual RAG chunk."
    )
    max_group_size_for_rag_chunk: int = Field(
        default=5,
        ge=1,
        description="Upper ceiling on the number of neighboring chunks grouped into a single RAG chunk."
    )
    objects_per_buffer: int = Field(
        default=500,
        gt=0,
        description="Buffer threshold count for in-memory batch processing before flushing."
    )
    rows_per_io_buffer: int = Field(
        default=500,
        gt=0,
        description="Number of rows per database I/O buffer before writing to storage."
    )

    # Video Processing
    video_segment_duration_minutes: float = Field(
        default=10.0,
        gt=0.0,
        description="Duration (in minutes) for each primary video processing segment."
    )
    video_overlap_minutes: float = Field(
        default=1.0,
        ge=0.0,
        description="Overlap duration (in minutes) between adjacent video segments."
    )
    video_max_duration_per_rag_chunk: float = Field(
        default=2.0,
        gt=0.0,
        description="Maximum allowable duration (in minutes) for an individual video RAG chunk."
    )
    video_max_words_per_rag_chunk: int = Field(
        default=300,
        gt=0,
        description="Maximum transcript word count allowed per video RAG chunk."
    )

    # Audio Processing
    audio_segment_duration_minutes: float = Field(
        default=10.0,
        gt=0.0,
        description="Duration (in minutes) for each primary audio processing segment."
    )
    audio_overlap_minutes: float = Field(
        default=1.0,
        ge=0.0,
        description="Overlap duration (in minutes) between adjacent audio segments."
    )
    audio_max_duration_per_rag_chunk: float = Field(
        default=2.0,
        gt=0.0,
        description="Maximum allowable duration (in minutes) for an individual audio RAG chunk."
    )
    audio_max_words_per_rag_chunk: int = Field(
        default=300,
        gt=0,
        description="Maximum transcript word count allowed per audio RAG chunk."
    )

    # Vector Similarity Thresholds
    gte_edge_vector_similar_threshold: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity score required to create a relationship edge between chunks."
    )
    gte_edge_vector_similar_top_k: int = Field(
        default=3,
        ge=1,
        description="Maximum number of top similar chunks to retrieve when creating relationship (vector_similar) edges."
    )
    gte_qdrant_point_score_threshold: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        description="Minimum search similarity threshold for Qdrant vector retrieval."
    )

    # Expert Query
    eq_max_lane_count: int = Field(
        default=3,
        ge=1,
        description="Maximum number of mapping lanes to explore during Expert Query retrieval."
    )
    eq_max_lane_entity: int = Field(
        default=3,
        ge=1,
        description="Maximum top-ranked entities selected per lane meeting the weight threshold."
    )
    eq_gte_lane_weight_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum weight score required to qualify an entity lane for chunk retrieval."
    )
    eq_max_lane_chunks: int = Field(
        default=5,
        ge=1,
        description="Maximum candidate chunks retained per lane following sparse retrieval."
    )
    eq_max_chunks: int = Field(
        default=5,
        ge=1,
        description="Final top-N chunks selected for context expansion, adjacent chunks, and vector similarity."
    )


class ProjectVariableCreateSchema(ProjectVariableBase):
    """Used when creating the project variables (defaults will fill missing keys)."""
    pass
