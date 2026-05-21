
class GRedisConstant:
    GRAXON_PREFIX = "graxon"
    TEMP = "temp"
    TAGS_PREFIX = "tags"
    EMBEDDINGS_PREFIX = "embeddings"
    SPARSE_EMBEDDING_PREFIX = "sparse_embedding"
    DIG_NODE_STATUS = "dig_node_status"
    DIG_NODE_STATUS_COMPLETED = "COMPLETED"
    DIG_NODE_STATUS_PENDING = "PENDING"
    SUPERVISOR_NODE = "supervisor"
    CHUNK_PARSER_NODE = "chunk_parser"
    LLM_NODE = "llm"
    EMBEDDING_NODE = "embedding"
    SPARSE_EMBEDDING_NODE = "sparse_embedding"
    RERANKER_NODE = "reranker"
    LEXICAL_ENGINE_NODE = "lexical_engine"
    VECTOR_DATABASE_NODE = "vector_database"
    GRAPH_DATABASE_NODE = "graph_database"
    SIMILARITY_SYNC_NODE = "similarity_sync"


class GRedisKeys:
    # Tags
    TAG_TEMP_KEY = f"{GRedisConstant.GRAXON_PREFIX}:{GRedisConstant.TEMP}:{GRedisConstant.TAGS_PREFIX}"
    TAG_KEY = f"{GRedisConstant.GRAXON_PREFIX}:{GRedisConstant.TAGS_PREFIX}"

    # Embeddings
    EMBEDDINGS_TEMP_KEY = f"{GRedisConstant.GRAXON_PREFIX}:{GRedisConstant.TEMP}:{GRedisConstant.EMBEDDINGS_PREFIX}"
    EMBEDDINGS_KEY = f"{GRedisConstant.GRAXON_PREFIX}:{GRedisConstant.EMBEDDINGS_PREFIX}"

    # Sparse Embeddings
    SPARSE_EMBEDDINGS_TEMP_KEY = f"{GRedisConstant.GRAXON_PREFIX}:{GRedisConstant.TEMP}:{GRedisConstant.SPARSE_EMBEDDING_PREFIX}"
    SPARSE_EMBEDDINGS_KEY = f"{GRedisConstant.GRAXON_PREFIX}:{GRedisConstant.SPARSE_EMBEDDING_PREFIX}"

    @staticmethod
    def get_dig_node_status_key(dig_node: str):
        return f"{GRedisConstant.GRAXON_PREFIX}:{GRedisConstant.DIG_NODE_STATUS}:{dig_node}"
