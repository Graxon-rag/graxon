
PROJECT_VARIABLES_DEFAULT_VALUES: list[dict[str, str]] = [
  {
    "key": "embedding_chunk_batch_size",
    "value": "30",
    "description": "Number of text chunks processed in a single batch during dense embedding generation."
  },
  {
    "key": "sparse_chunk_batch_size",
    "value": "30",
    "description": "Number of text chunks processed in a single batch during sparse (BM25/SPLADE) embedding generation."
  },
  {
    "key": "llm_tag_extraction_batch_size",
    "value": "10",
    "description": "Number of chunks sent per batch to the LLM for entity and tag extraction."
  },
  {
    "key": "delay_between_chunk_processing_seconds",
    "value": "10",
    "description": "Cooldown delay (in seconds) between chunk processing batches to prevent API rate limiting."
  },
  {
    "key": "chunk_size",
    "value": "1500",
    "description": "Target character count per document chunk."
  },
  {
    "key": "chunk_overlap",
    "value": "200",
    "description": "Number of overlapping characters between consecutive chunks to maintain context."
  },
  {
    "key": "max_chunks",
    "value": "10000",
    "description": "Maximum number of total chunks allowed for a single document or ingestion run."
  },
  {
    "key": "max_chunk_size_mb",
    "value": "4",
    "description": "Maximum allowed size per chunk in megabytes (MB)."
  },
  {
    "key": "max_pages_per_batch",
    "value": "10",
    "description": "Number of document pages parsed per batch during ingestion."
  },
  {
    "key": "tail_carry_chars",
    "value": "500",
    "description": "Number of trailing characters carried over across page boundaries to avoid mid-sentence splits."
  },
  {
    "key": "group_size_for_rag_chunk",
    "value": "3",
    "description": "Default number of neighboring chunks grouped together to form a contextual RAG chunk."
  },
  {
    "key": "max_group_size_for_rag_chunk",
    "value": "5",
    "description": "Upper ceiling on the number of neighboring chunks grouped into a single RAG chunk."
  },
  {
    "key": "objects_per_buffer",
    "value": "500",
    "description": "Buffer threshold count for in-memory batch processing before flushing."
  },
  {
    "key": "rows_per_io_buffer",
    "value": "500",
    "description": "Number of rows per database I/O buffer before writing to storage."
  },
  {
    "key": "video_segment_duration_minutes",
    "value": "10.0",
    "description": "Duration (in minutes) for each primary video processing segment."
  },
  {
    "key": "video_overlap_minutes",
    "value": "1.0",
    "description": "Overlap duration (in minutes) between adjacent video segments."
  },
  {
    "key": "video_max_duration_per_rag_chunk",
    "value": "2.0",
    "description": "Maximum allowable duration (in minutes) for an individual video RAG chunk."
  },
  {
    "key": "video_max_words_per_rag_chunk",
    "value": "300",
    "description": "Maximum transcript word count allowed per video RAG chunk."
  },
  {
    "key": "audio_segment_duration_minutes",
    "value": "10.0",
    "description": "Duration (in minutes) for each primary audio processing segment."
  },
  {
      "key": "audio_overlap_minutes",
      "value": "1.0",
      "description": "Overlap duration (in minutes) between adjacent audio segments."
  },
  {
      "key": "audio_max_duration_per_rag_chunk",
      "value": "2.0",
      "description": "Maximum allowable duration (in minutes) for an individual audio RAG chunk."
  },
  {
      "key": "audio_max_words_per_rag_chunk",
      "value": "300",
      "description": "Maximum transcript word count allowed per audio RAG chunk."
  },
  {
    "key": "gte_edge_vector_similar_threshold",
    "value": "0.75",
    "description": "Minimum cosine similarity score required to create a relationship edge between chunks."
  },
  {
    "key": "gte_qdrant_point_score_threshold",
    "value": "0.45",
    "description": "Minimum search similarity threshold for Qdrant vector retrieval."
  },
  {
    "key": "eq_max_lane_count",
    "value": "3",
    "description": "Maximum number of mapping lanes to explore during Expert Query retrieval."
  },
  {
    "key": "eq_max_lane_entity",
    "value": "3",
    "description": "Maximum top-ranked entities selected per lane meeting the weight threshold."
  },
  {
    "key": "eq_gte_lane_weight_threshold",
    "value": "0.7",
    "description": "Minimum weight score required to qualify an entity lane for chunk retrieval."
  },
  {
    "key": "eq_max_lane_chunks",
    "value": "5",
    "description": "Maximum candidate chunks retained per lane following sparse retrieval."
  },
  {
    "key": "eq_max_chunks",
    "value": "5",
    "description": "Final top-N chunks selected for context expansion, adjacent chunks, and vector similarity."
  },
]
