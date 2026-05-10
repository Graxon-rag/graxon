
class GNeo4jEdges:
    # Structure
    HAS_CHUNK = "HAS_CHUNK"
    HAS_DOCUMENT = "HAS_DOCUMENT"
    HAS_PROJECT = "HAS_PROJECT"

    # Sequential
    PREV = "PREV"
    NEXT = "NEXT"

    # Semantic links (Chunk → intermediate node)
    HAS_TAG = "HAS_TAG"
    HAS_ENTITY = "HAS_ENTITY"
    HAS_CONCEPT = "HAS_CONCEPT"
    HAS_KEYWORD = "HAS_KEYWORD"
    HAS_PHRASE = "HAS_PHRASE"
    HAS_ACRONYM = "HAS_ACRONYM"

    # Keep these only if you need precomputed similarity scores
    VECTOR_SIMILARITY = "VECTOR_SIMILARITY"  # with {score: 0.91}
    REFERENCES = "REFERENCES"         # explicit doc cross-refs

    SHARES_ENTITY = "SHARES_ENTITY"
    SHARES_CONCEPT = "SHARES_CONCEPT"
    SHARES_KEYWORD = "SHARES_KEYWORD"
    SHARES_PHRASE = "SHARES_PHRASE"
    SHARES_ACRONYM = "SHARES_ACRONYM"


class GN4jNodes:
    CHUNK = "Chunk"
    DOCUMENT = "Document"
    ORGANIZATION = "Organization"
    PROJECT = "Project"
    TAG = "Tag"
    ENTITY = "Entity"
    CONCEPT = "Concept"
    KEYWORD = "Keyword"
    PHRASE = "Phrase"
    ACRONYM = "Acronym"


class GN4jNodesIds:
    CHUNK_ID = "id"
    DOCUMENT_ID = "id"
    ORGANIZATION_ID = "id"
    PROJECT_ID = "id"
    TAG_ID = "id"
    ENTITY_ID = "id"
    CONCEPT_ID = "id"
    KEYWORD_ID = "id"
    PHRASE_ID = "id"
    ACRONYM_ID = "id"
