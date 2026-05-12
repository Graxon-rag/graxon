
class GRedisConstant:
    GRAXON_PREFIX = "graxon"
    TEMP = "temp"
    TAGS_PREFIX = "tags"
    EMBEDDINGS_PREFIX = "embeddings"
    SPARSE_EMBEDDING_PREFIX = "sparse_embedding"


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
