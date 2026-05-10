class N4jTagInterface:
    id = "id" 
    type = "type"
    value = "value"         # stored as lowercase normalized
    frequency = "frequency"  # how many chunks reference this tag


class N4jEntityInterface:
    id = "id"
    type = "type"
    value = "value"   # normalized name e.g. "openai"
    label = "label"     # entity type: ORG, PERSON, GPE, PRODUCT etc.
    frequency = "frequency"


class N4jConceptInterface:
    id = "id"
    type = "type"
    value = "value"
    frequency = "frequency"


class N4jKeywordInterface:
    id = "id"
    type = "type"
    value = "value"
    frequency = "frequency"


class N4jPhraseInterface:
    id = "id"
    type = "type"
    value = "value"
    frequency = "frequency"


class N4jAcronymInterface:
    id = "id"
    type = "type"
    value = "value"   # stored uppercase e.g. "RAG"
    expansion = "expansion"  # "Retrieval Augmented Generation"
    frequency = "frequency"


class N4jChunkTagEdgeInterface:
    weight = "weight"
    frequency = "frequency"


class N4jChunkEntityEdgeInterface:
    weight = "weight"
    frequency = "frequency"


class N4jChunkConceptEdgeInterface:
    weight = "weight"
    frequency = "frequency"


class N4jChunkKeywordEdgeInterface:
    weight = "weight"
    frequency = "frequency"


class N4jChunkPhraseEdgeInterface:
    weight = "weight"
    frequency = "frequency"


class N4jChunkAcronymEdgeInterface:
    weight = "weight"
    frequency = "frequency"
