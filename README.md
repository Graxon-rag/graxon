# graxon

## Spacy

```py
spacy download en_core_web_sm
```

## Lexical Engine

Entity Extraction (NER) — Detects shared named entities like people, organizations, products, and technologies across chunks to build high-confidence semantic relationships.
Concept Extraction (Noun Phrases) — Extracts meaningful noun phrases and technical concepts shared between chunks to connect semantically related ideas.
TF-IDF Keyword Linking — Uses TF-IDF scoring to identify rare but important keywords that appear across multiple chunks while filtering common noise words.
Phrase Bridge Detection — Generates exact n-gram phrase matches between chunks to capture strong lexical overlap and repeated terminology.
Acronym Resolution — Detects acronym definitions and links them to later acronym usage across the document for better contextual understanding.
Edge Construction — Converts shared entities, concepts, keywords, phrases, and acronyms into graph edges connecting related chunks.
Edge Deduplication — Removes duplicate or weaker edges to keep the graph cleaner, more meaningful, and efficient for traversal.

Entity Extraction (NER) — Identifies shared named entities such as people, organizations, technologies, and products across chunks. This helps create strong semantic links between chunks discussing the same real-world subject and improves graph-based retrieval accuracy.
Concept Extraction (Noun Phrases) — Extracts meaningful noun phrases and technical concepts shared between chunks. It helps connect semantically related ideas even when exact keywords differ, improving topic grouping and contextual understanding.
TF-IDF Keyword Linking — Uses TF-IDF scoring to detect rare but informative keywords that appear across multiple chunks while filtering common noise words. This highlights statistically important terms that help strengthen semantic relationships.
Phrase Bridge Detection — Detects exact shared n-gram phrases between chunks to capture repeated terminology and strong lexical overlap. This is especially useful for technical, scientific, and domain-specific documents where repeated phrases carry important meaning.
Acronym Resolution — Detects acronym definitions and links them to later acronym usage throughout the document. This improves long-document comprehension by connecting abbreviated references back to their original meaning.
Edge Construction — Converts all detected lexical relationships into graph edges connecting related chunks. These edges form the foundation of the semantic document graph used for retrieval, traversal, and contextual reasoning.
Edge Deduplication — Removes duplicate or weaker relationships while preserving the strongest semantic connections. This keeps the graph cleaner, more efficient, and easier to traverse during retrieval and ranking operations.
