import re
from pydantic import BaseModel, Field
from app.utils.logger import logger
import spacy
from app.constants.neo4j import GNeo4jEdges
from typing import List
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer


# Stopwords
# Core English stopwords (NLTK english list) + domain-agnostic noise words
STOP_WORDS = {
    # articles, pronouns, prepositions, conjunctions
    "a", "an", "the", "and", "or", "but", "if", "in", "on", "at", "to", "for", "of", "with", 
    "by", "from", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", 
    "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "shall", 
    "can", "not", "no", "nor", "so", "yet", "both", "either", "neither", "each", "every", 
    "all", "any", "few", "more", "most", "other", "some", "such", "than", "then", "that", 
    "this", "these", "those", "what", "which", "who", "whom", "when", "where", "why", "how", 
    "its", "our", "your", "his", "her", "their", "we", "they", "he", "she", "it", "you", "i", 
    "me", "him", "us", "them", "my", "mine", "his", "hers", "ours", "yours", "theirs", 
    "am", "into", "up", "out", "about", "after", "before", "between", "through", "during", 
    "about", "above", "below", "over", "under", "again", "further", "once", "here", "there", 
    "while", "although", "though", "because", "since", "until", "unless", "whether", 
    # noise verbs and adjectives that slip into bridges
    "also", "however", "therefore", "thus", "hence", 
    "often", "usually", "generally", "typically", 
    "using", "used", "use", "uses", "based", "given", 
    "made", "make", "makes", "allow", "allows", "provide", 
    "provides", "include", "includes", "result", "results", 
    "approach", "method", "system", "different", "various", 
    "large", "small", "high", "low", "real", "time", "data", 
    "first", "second", "third", "well", "show", "shows", 
    "need", "needs", "mean", "means", "call", "calls", 
    "just", "like", "much", "many", "without", "within", 
    "across", "along", "around", "behind", "beside", 
}

# Words that are almost always nouns/proper nouns in technical text
_TECHNICAL_NOUN_PATTERN = re.compile(
    r'\b([A-Z][a-z]{2,}|[a-z]{4,}(?:tion|ment|ism|ity|ing|ence|ance|ness|ture|ware|work|base|work))\b'
)

_DEF_RE = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([A-Z]{2,6})\)')


class LEChunk(BaseModel):
    chunk_id: str
    chunk_number: int
    text: str


class LexicalEdge(BaseModel):
    source: str
    target: str
    edge_type: str
    label: str
    weight: float


class LexicalResult(BaseModel):
    edges: list[LexicalEdge] = Field(default_factory=list)
    acronyms: dict[str, dict] = Field(default_factory=dict)
    filtered_noise: list[str] = Field(default_factory=list)


class LexicalEngine:
    def __init__(self):
        try:
            self._nlp = spacy.load("en_core_web_sm", disable=["lemmatizer"])
            self.SPACY_AVAILABLE = True
            print("✓ spaCy loaded — full NER + noun phrase mode\n")

        except Exception:
            self.SPACY_AVAILABLE = False
            print("⚠  spaCy not available — using regex fallback (install spaCy for best results)\n")

    def run_lexical_engine(self, chunks: list[LEChunk]) -> LexicalResult:
        try:
            result = LexicalResult()

            # Step 1 — entities + concepts
            if self.SPACY_AVAILABLE:
                entity_map, concept_map = self._extract_spacy(chunks)
            else:
                entity_map, concept_map = self._extract_regex_fallback(chunks)

            shared_entities = {e: ids for e, ids in entity_map.items() if len(ids) >= 2}
            shared_concepts = {c: ids for c, ids in concept_map.items() if len(ids) >= 2}
            result.edges += self._bridge_to_edges(shared_entities, GNeo4jEdges.SHARES_ENTITY, 1.5)
            result.edges += self._bridge_to_edges(shared_concepts, GNeo4jEdges.SHARES_CONCEPT, 1.2)

            # Step 2 — TF-IDF keywords
            keyword_map, noise = self.extract_tfidf_keywords(chunks)
            result.edges += self._bridge_to_edges(keyword_map, GNeo4jEdges.SHARES_KEYWORD, 1.0)
            result.filtered_noise = noise

            # Step 3 — phrases
            phrase_map = self._extract_phrase_bridges(chunks)
            result.edges += self._bridge_to_edges(phrase_map, GNeo4jEdges.SHARES_PHRASE, 1.3)

            # Step 4 — acronyms
            acronyms = self._extract_acronyms(chunks)
            result.acronyms = acronyms
            result.edges += self._acronym_to_edges(acronyms, GNeo4jEdges.SHARES_ACRONYM, 1.4)

            result.edges = self._deduplicate(result.edges)
            return result
        except Exception as e:
            logger.error({"message": "Failed to run lexical engine", "error": str(e)})
            raise e

    #  NER + NOUN PHRASES  (spaCy path)
    def _extract_spacy(self, chunks: List[LEChunk]):
        """Returns entity_map and concept_map using spaCy."""

        try:
            entity_map: dict[str, set] = defaultdict(set)
            concept_map: dict[str, set] = defaultdict(set)

            docs = self._nlp.pipe([c.text for c in chunks], batch_size=32)
            for chunk, doc in zip(chunks, docs):
                for ent in doc.ents:
                    label = ent.text.strip().lower()
                    if len(label) >= 3 and label not in STOP_WORDS and not label.isdigit():
                        entity_map[label].add(chunk.chunk_id)

                for np_ in doc.noun_chunks:
                    phrase = re.sub(r"\s+", " ", np_.text.strip().lower())
                    words = phrase.split()
                    if 2 <= len(words) <= 5:
                        content = [w for w in words if w not in STOP_WORDS and len(w) > 2]
                        if content:
                            concept_map[phrase].add(chunk.chunk_id)

            return dict(entity_map), dict(concept_map)

        except Exception as e:
            logger.error({"message": "Failed to run spaCy agent", "error": str(e)})
            return {}, {}

    # fallback — Regex-based noun approximation
    def _extract_regex_fallback(self, chunks: list[LEChunk]):
        """Approximate NER + noun phrases using regex when spaCy unavailable."""
        try:
            entity_map: dict[str, set] = defaultdict(set)
            concept_map: dict[str, set] = defaultdict(set)

            for chunk in chunks:
                # Capitalized terms as "entities"
                for match in re.finditer(r'\b[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,})*\b', chunk.text):
                    label = match.group().strip().lower()
                    if label not in STOP_WORDS and len(label) >= 4:
                        entity_map[label].add(chunk.chunk_id)

                # Technical nouns as "concepts"
                words = re.findall(r'\b[a-zA-Z]{4,}\b', chunk.text.lower())
                nouns = [w for w in words if w not in STOP_WORDS and _TECHNICAL_NOUN_PATTERN.match(w)]
                # Build bigrams from nouns
                for i in range(len(nouns) - 1):
                    phrase = f"{nouns[i]} {nouns[i + 1]}"
                    concept_map[phrase].add(chunk.chunk_id)

            return dict(entity_map), dict(concept_map)
        except Exception as e:
            logger.error({"message": "Failed to run regex agent", "error": str(e)})
            return {}, {}

    # TF-IDF RARE KEYWORD BRIDGES
    def extract_tfidf_keywords(self, chunks: list[LEChunk]):
        """
        Finds rare, meaningful nouns using TF-IDF.
        min_df=2  : must appear in at least 2 chunks
        max_df=0.6: ignore words in >60% of chunks (too common)
        sublinear_tf: dampens high-frequency words
        """
        try:
            texts = [c.text for c in chunks]

            # Build noun-only vocab first (POS filter via spaCy or regex)
            if self.SPACY_AVAILABLE:
                allowed_nouns = set()
                for doc in self._nlp.pipe(texts, batch_size=32):
                    for token in doc:
                        w = token.text.lower()
                        if token.pos_ in ("NOUN", "PROPN") and len(w) >= 4 and w not in STOP_WORDS:
                            allowed_nouns.add(w)
                vocabulary = list(allowed_nouns) if allowed_nouns else None
            else:
                # Regex fallback: keep words matching technical noun patterns
                vocabulary = None   # let TF-IDF decide, stopwords will filter

            vectorizer = TfidfVectorizer(
                vocabulary=vocabulary,
                stop_words=list(STOP_WORDS),
                min_df=2,
                max_df=0.6,
                sublinear_tf=True,
                token_pattern=r'\b[a-zA-Z]{4,}\b',
            )

            try:
                matrix = vectorizer.fit_transform(texts)
            except ValueError:
                return {}, []

            feature_names = vectorizer.get_feature_names_out()
            keyword_map: dict[str, set] = defaultdict(set)

            # Track what got filtered out (for display)
            all_raw_words = set(
                w.lower() for c in chunks
                for w in re.findall(r'\b[a-zA-Z]{4,}\b', c.text)
                if w.lower() not in STOP_WORDS
            )
            tfidf_vocab = set(feature_names)
            noise_caught = sorted(all_raw_words - tfidf_vocab - STOP_WORDS)[:15]

            cx = matrix.tocsc()
            for col_idx, word in enumerate(feature_names):
                rows = cx.getcol(col_idx).nonzero()[0]
                if len(rows) >= 2:
                    for row_idx in rows:
                        keyword_map[word].add(chunks[row_idx].chunk_id)

            return dict(keyword_map), noise_caught
        except Exception as e:
            logger.error({"message": "Failed to run TF-IDF agent", "error": str(e)})
            return {}, []

    # STEP 3 — EXACT N-GRAM PHRASE BRIDGES

    def _extract_phrase_bridges(self, chunks: list[LEChunk], n: int = 3, max_share: int = 4):
        try:
            phrase_map: dict[str, set] = defaultdict(set)

            for chunk in chunks:
                words = re.findall(r'\b[a-zA-Z]\w+\b', chunk.text.lower())
                words = [w for w in words if w not in STOP_WORDS]
                grams = [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]
                for gram in set(grams):
                    phrase_map[gram].add(chunk.chunk_id)

            return {p: ids for p, ids in phrase_map.items() if 1 < len(ids) <= max_share}
        except Exception as e:
            logger.error({"message": "Failed to run phrase agent", "error": str(e)})
            return {}

    # ACRONYM EXTRACTION

    def _extract_acronyms(self, chunks: list[LEChunk]):
        try:
            definitions = {}
            for chunk in chunks:
                for full, short in _DEF_RE.findall(chunk.text):
                    definitions[short] = {
                        "full": full.strip(),
                        "defined_in": chunk.chunk_id,
                        "used_in": [],
                    }

            for short, info in definitions.items():
                pat = re.compile(rf'\b{re.escape(short)}\b')
                for chunk in chunks:
                    if chunk.chunk_id != info["defined_in"] and pat.search(chunk.text):
                        info["used_in"].append(chunk.chunk_id)

            return definitions
        except Exception as e:
            logger.error({"message": "Failed to run acronym agent", "error": str(e)})
            return {}

    # EDGE BUILDER

    def _bridge_to_edges(self, bridge_map, edge_type: str, weight: float) -> list[LexicalEdge]:
        try:
            edges = []
            for label, ids in bridge_map.items():
                sorted_ids = sorted(ids)
                for i in range(len(sorted_ids)):
                    for j in range(i + 1, len(sorted_ids)):
                        edges.append(LexicalEdge(
                            source=sorted_ids[i],
                            target=sorted_ids[j],
                            edge_type=edge_type,
                            label=label,
                            weight=weight,
                        ))
            return edges
        except Exception as e:
            logger.error({"message": "Failed to run bridge agent", "error": str(e)})
            return []

    def _acronym_to_edges(self, acronyms, edge_type: str, weight: float) -> list[LexicalEdge]:
        try:
            edges = []
            for short, info in acronyms.items():
                for usage_id in info["used_in"]:
                    edges.append(LexicalEdge(
                        source=info["defined_in"],
                        target=usage_id,
                        edge_type=edge_type,
                        label=short,
                        weight=weight,
                    ))
            return edges
        except Exception as e:
            logger.error({"message": "Failed to run acronym agent", "error": str(e)})
            return []

    def _deduplicate(self, edges: list[LexicalEdge]) -> list[LexicalEdge]:
        best = {}
        for e in edges:
            key = (e.source, e.target, e.edge_type)
            if key not in best or e.weight > best[key].weight:
                best[key] = e
        return list(best.values())
