from .index import STOP_WORDS, _TECHNICAL_NOUN_PATTERN
from app.constants.neo4j import GNeo4jEdges
from collections import defaultdict
from typing import List, Tuple
from pydantic import BaseModel
import spacy
import re

_CAMEL_RE = re.compile(r'(?<=[a-z])(?=[A-Z])')


class QueryAnalysis(BaseModel):
    raw_query: str
    tokens: List[str]
    entities: List[dict]
    noun_chunks: List[str]
    is_acronym_query: bool
    is_single_token: bool
    is_multi_word: bool
    lane_priority: List[Tuple[str, float]]
    normalized_query_for_lane: dict[str, str]   # lane → normalized query string for that lane


class LexicalEngineQuery:
    def __init__(self):
        try:
            self._nlp = spacy.load("en_core_web_sm", disable=["lemmatizer"])
            self.SPACY_AVAILABLE = True
        except Exception:
            self.SPACY_AVAILABLE = False

    def analyze_query(self, query: str) -> QueryAnalysis:
        query = query.strip()
        tokens = [t for t in query.lower().split() if t not in STOP_WORDS]
        is_single_token = len(tokens) == 1
        is_multi_word = len(tokens) > 2

        cleaned = query.replace(".", "").strip()
        is_acronym_query = bool(re.fullmatch(r'[A-Z]{2,6}', cleaned))

        entities = []
        noun_chunks = []

        if self.SPACY_AVAILABLE:
            doc = self._nlp(query)
            entities = [
                {"text": ent.text, "label": ent.label_}
                for ent in doc.ents
            ]
            noun_chunks = [
                chunk.text.lower()
                for chunk in doc.noun_chunks
                if chunk.text.lower() not in STOP_WORDS
                and len(chunk.text.split()) > 1
            ]

        lane_priority = self._resolve_lane_priority(
            is_acronym_query=is_acronym_query,
            is_single_token=is_single_token,
            is_multi_word=is_multi_word,
            entities=entities,
            noun_chunks=noun_chunks,
            tokens=tokens,
        )

        all_lanes = [
            GNeo4jEdges.HAS_TAG,
            GNeo4jEdges.HAS_KEYWORD,
            GNeo4jEdges.HAS_PHRASE,
            GNeo4jEdges.HAS_ENTITY,
            GNeo4jEdges.HAS_CONCEPT,
            GNeo4jEdges.HAS_ACRONYM,
        ]
        normalized_query_for_lane = {
            lane: self.normalize_query_for_lane(query, lane)
            for lane in all_lanes
        }

        return QueryAnalysis(
            raw_query=query,
            tokens=tokens,
            entities=entities,
            noun_chunks=noun_chunks,
            is_acronym_query=is_acronym_query,
            is_single_token=is_single_token,
            is_multi_word=is_multi_word,
            lane_priority=lane_priority,
            normalized_query_for_lane=normalized_query_for_lane,
        )

    def _resolve_lane_priority(
        self,
        is_acronym_query: bool,
        is_single_token: bool,
        is_multi_word: bool,
        entities: List[dict],
        noun_chunks: List[str],
        tokens: List[str],
    ) -> List[Tuple[str, float]]:

        # Each lane gets a score — highest scores go first
        scores: dict[str, float] = defaultdict(float)

        # --- Hard signals (clear structural indicators) ---

        if is_acronym_query:
            scores[GNeo4jEdges.HAS_ACRONYM] += 3.0

        if entities:
            scores[GNeo4jEdges.HAS_ENTITY] += 2.0 * len(entities)

        if noun_chunks:
            scores[GNeo4jEdges.HAS_PHRASE] += 1.5 * len(noun_chunks)
            # Noun chunks also suggest concepts when they're abstract
            scores[GNeo4jEdges.HAS_CONCEPT] += 0.5 * len(noun_chunks)

        # --- Soft signals (token-level heuristics) ---

        if is_single_token:
            scores[GNeo4jEdges.HAS_KEYWORD] += 2.0
            scores[GNeo4jEdges.HAS_TAG] += 1.0

        if is_multi_word and not noun_chunks:
            # Multi-word but spaCy found no noun chunks → likely a concept/abstract query
            scores[GNeo4jEdges.HAS_CONCEPT] += 1.5
            scores[GNeo4jEdges.HAS_KEYWORD] += 0.5

        # Technical noun pattern in tokens → keyword signal
        technical_hits = sum(
            1 for t in tokens
            if _TECHNICAL_NOUN_PATTERN.match(t)
        )
        if technical_hits:
            scores[GNeo4jEdges.HAS_KEYWORD] += 0.8 * technical_hits

        # Give every lane a baseline so nothing is completely excluded in advanced mode
        for lane in [
            GNeo4jEdges.HAS_TAG,
            GNeo4jEdges.HAS_KEYWORD,
            GNeo4jEdges.HAS_PHRASE,
            GNeo4jEdges.HAS_ENTITY,
            GNeo4jEdges.HAS_CONCEPT,
            GNeo4jEdges.HAS_ACRONYM,
        ]:
            scores[lane] += 0.1

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked

    def normalize_node_value(self, value: str, edge_type: str) -> str:
        """
        Normalize a stored node value for embedding comparison.
        edge_type is one of GNeo4jEdges.HAS_*
        """
        if edge_type == GNeo4jEdges.HAS_ACRONYM:
            return value.replace(".", "").strip().upper()

        if edge_type == GNeo4jEdges.HAS_ENTITY:
            # preserve meaningful casing, just fix separators
            normalized = value.replace("_", " ").replace("-", " ")
            # collapse multiple spaces
            return re.sub(r'\s+', ' ', normalized).strip()

        # TAG, KEYWORD, PHRASE, CONCEPT
        # 1. camelCase split
        value = _CAMEL_RE.sub(' ', value)
        # 2. replace separators
        value = value.replace("_", " ").replace("-", " ")
        # 3. lowercase
        value = value.lower()
        # 4. collapse spaces
        value = re.sub(r'\s+', ' ', value).strip()
        # 5. remove stopwords for TAG/KEYWORD only (phrases/concepts need their words)
        if edge_type in (GNeo4jEdges.HAS_TAG, GNeo4jEdges.HAS_KEYWORD):
            tokens = [t for t in value.split() if t not in STOP_WORDS]
            value = " ".join(tokens)

        return value

    def normalize_query_for_lane(self, query: str, edge_type: str) -> str:
        """
        Normalize the query to match what stored node values look like per lane.
        """
        if edge_type == GNeo4jEdges.HAS_ACRONYM:
            cleaned = query.replace(".", "").strip()
            # only return as acronym if it looks like one
            if re.fullmatch(r'[A-Z]{2,6}', cleaned):
                return cleaned.upper()
            return query.strip()

        if edge_type == GNeo4jEdges.HAS_ENTITY:
            # keep casing, just clean separators
            return re.sub(r'\s+', ' ', query.replace("_", " ")).strip()

        # TAG, KEYWORD, PHRASE, CONCEPT
        query = _CAMEL_RE.sub(' ', query)
        query = query.replace("_", " ").replace("-", " ").lower()
        query = re.sub(r'\s+', ' ', query).strip()

        if edge_type in (GNeo4jEdges.HAS_TAG, GNeo4jEdges.HAS_KEYWORD):
            tokens = [t for t in query.split() if t not in STOP_WORDS]
            query = " ".join(tokens)

        return query
