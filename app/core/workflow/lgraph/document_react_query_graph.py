"""
DocumentQueryGraph — ReAct-style agentic RAG pipeline.

Instead of a fixed quick/smart/expert pipeline, a single agent node is given
tools for every retrieval primitive (vector DB, graph-DB lexical lanes,
vector-similar-chunk lookup, reranking) and decides for itself which to call,
in what order, and how many times, based on the query.

IMPORTANT ASSUMPTION: `WorkflowLLM.llm(...)` must return a LangChain
`BaseChatModel`-compatible object supporting `.bind_tools()` and
`.astream(messages)` over a list of `BaseMessage`. Tool-calling and streaming
both depend on this. If your current wrapper only exposes `.ainvoke(prompt=...)`
with a raw string, it needs to be upgraded to the standard interface first.

Streaming/events for the UI: don't manually emit events inside the node.
Because the model is called with `.astream(messages, config=config)` and tools
are invoked with `.ainvoke(args, config=config)`, LangGraph automatically
propagates callbacks up to whoever runs `workflow.astream_events(...)` at the
top level (see the `stream_query_documents` example at the bottom of this
file). That top-level consumer gets `on_chat_model_stream` (thinking/token),
`on_tool_start` (tool_call), `on_tool_end` (tool_result), and `on_chain_end`
for AGENT_NODE (final answer + metadata) for free.
"""

from app.core.schemas.chunk_schema import ChunkPrevNextVecSimilaritySchema, ChunkPrevNextSchema, ChunkVecSimilarity
from typing import TypedDict, Annotated, Dict, cast, Tuple, Optional, List, Union, Sequence, TypeVar, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from .prompts.query_expansion_prompt import QUERY_EXPANSION_PROMPT, QueryExpansionResponse
from app.core.lexical_engine.query import LexicalEngineQuery, QueryAnalysis
from ...schemas.project_config_schema import ProjectConfigDetailGetSchema
from langchain_core.language_models.chat_models import BaseChatModel
from app.core.schemas.graph_schema import N4jCommonEdgeChunksSchema
from qdrant_client.conversions.common_types import QueryResponse
from ..provider import WorkflowEmbedder, WorkflowSparseEmbedder
from app.core.qdrant.retrieval import QDrantRetrieval
from ..provider import WorkflowReranker, WorkflowLLM
from app.core.neo4j.common import GN4jMappingClient
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from app.core.schemas import query_schema as qs
from langchain_core.tools import tool, BaseTool
from langchain_core.documents import Document
from qdrant_client.models import ScoredPoint
from app.constants.neo4j import GNeo4jEdges
from app.core.neo4j.chunk import GN4jChunk
from fastembed import SparseEmbedding
from app.utils.logger import logger
from app.config.env import Env
import uuid

SUPERVISOR_AGENT = "supervisor_agent"
QUERY_EXPANSION_AGENT = "query_expansion_agent"
AGENT_NODE = "agent_node"

MAX_AGENT_TURNS = 6


def merge_optional(a, b):
    return b if b is not None else a


SPARSE_LANES = {
    GNeo4jEdges.HAS_TAG,
    GNeo4jEdges.HAS_KEYWORD,
    GNeo4jEdges.HAS_ACRONYM,
}

DENSE_LANES = {
    GNeo4jEdges.HAS_PHRASE,
    GNeo4jEdges.HAS_CONCEPT,
    GNeo4jEdges.HAS_ENTITY,
}

# Any chunk shape that carries chunk_id / text / prev_chunk / next_chunk / point_score
ChunkLike = Union[ChunkPrevNextSchema, ChunkPrevNextVecSimilaritySchema]
TChunk = TypeVar("TChunk", ChunkPrevNextSchema, ChunkPrevNextVecSimilaritySchema)


AGENT_SYSTEM_PROMPT = """You are an expert document-analysis assistant. You answer questions about a \
specific document using retrieval tools — you never rely on outside knowledge or guesses.

Available tools:
- vector_search: semantic (dense + sparse hybrid) search over the document's chunks. Use this first \
for most questions.
- lexical_lane_search: graph-based lookup by tags, keywords, phrases, named entities, concepts, and \
acronyms. Use this when vector_search seems to miss exact terms, numbers, table values, or named \
entities — it's often stronger for precise factual lookups than pure semantic search.
- get_similar_chunks: given chunk_ids you already retrieved, finds other chunks elsewhere in the \
document that are semantically related (e.g. cross-references, repeated mentions of the same figure).
- rerank_chunks: given chunk_ids you've gathered from one or more searches, reorders them by true \
relevance to the query. Use this before answering whenever you've pulled chunks from more than one \
search, so you know which ones actually matter.

Guidelines:
- Call tools until you have enough grounded evidence to answer directly. Don't stop after one search \
if the query needs corroboration (e.g. totals, comparisons, anything that could appear in more than \
one place in the document) — try both vector_search and lexical_lane_search and compare results.
- If a fact or number isn't found in any tool result, say so plainly instead of guessing.
- Cite chunk numbers inline when useful (e.g. "per chunk 47 ...").
- Query hint from caller — query_type: {query_type}, query_depth: {query_depth}. Treat this only as a \
rough guide for how much tool-calling effort is warranted: quick = light effort (1-2 tool calls), \
expert = thorough, cross-checked effort (multiple tools, verify agreement across sources).

Once you're confident in your answer, respond with a final, direct, plain-text answer and do NOT call \
any more tools."""


class ReActDQGState(TypedDict):
    request_id: str
    org_id: str
    project_id: uuid.UUID
    project_config: ProjectConfigDetailGetSchema
    ep_model_key: str
    query: str
    top_k: int
    query_type: qs.QueryType
    query_depth: qs.QueryDepth
    document_id: uuid.UUID | None

    queries: list[str] | None
    metadata: list[dict] | None
    eq_analysis: Optional[QueryAnalysis] | None
    eq_lexical_engine_chunk_ids: set[Tuple[str, float]] | None

    answer: str | dict | None


class DocumentQueryReActGraph():
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.q_retrieval = QDrantRetrieval(org_id=org_id, project_id=project_id)
        self._lexical_engine = LexicalEngineQuery()
        self._chunk_n4j = GN4jChunk(org_id=org_id, project_id=project_id)
        self._n4j_mapping_client = GN4jMappingClient(org_id=org_id, project_id=project_id)

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------
    def build_graph(self):
        try:
            graph = StateGraph(ReActDQGState)

            graph.add_node(SUPERVISOR_AGENT, self._supervisor)
            graph.add_node(QUERY_EXPANSION_AGENT, self._query_expansion)
            graph.add_node(AGENT_NODE, self._agent_node)

            graph.add_edge(START, SUPERVISOR_AGENT)
            graph.add_edge(SUPERVISOR_AGENT, QUERY_EXPANSION_AGENT)
            graph.add_edge(QUERY_EXPANSION_AGENT, AGENT_NODE)
            graph.add_edge(AGENT_NODE, END)

            workflow = graph.compile()
            logger.info({"message": "Query Graph built successfully"})

            return workflow
        except Exception as e:
            logger.error({"message": "Failed to build graph", "error": str(e)})
            raise e

    # ------------------------------------------------------------------
    # Shared model-provisioning helpers
    # ------------------------------------------------------------------
    def _get_llm(self, project_config: ProjectConfigDetailGetSchema, structured_output=None) -> BaseChatModel:
        llm_model = project_config.llm_model
        llm_model_credential = project_config.llm_model_credential

        if llm_model is None or llm_model_credential is None:
            logger.warning({"message": "LLM Model is not configured", "org_id": self.org_id, "project_id": self.project_id})
            raise ValueError("LLM Model is not configured")

        # Initialize your custom wrapper (returns a BaseLLM instance)
        llm = WorkflowLLM.llm(
            provider=llm_model.provider,
            api_key=llm_model_credential.api_key,
            model=llm_model.model_id,
        )

        # Bind the structured output using wrapper's method
        if structured_output is not None:
            llm = llm.with_structured_output(structured_output)

        # Extract, cast, and return the underlying LangChain BaseChatModel
        return cast(BaseChatModel, llm.get_langchain_llm())

    def _get_embedder(self, project_config: ProjectConfigDetailGetSchema):
        embedding_model = project_config.embedding_model
        embedding_model_credential = project_config.embedding_model_credential
        if embedding_model is None or embedding_model_credential is None:
            logger.error({"message": "Embedding Model is not configured", "org_id": self.org_id, "project_id": self.project_id})
            raise ValueError("Embedding Model or Embedding Model Credential is not configured")

        return WorkflowEmbedder.embedder(
            provider=embedding_model.provider,
            api_key=embedding_model_credential.api_key,
            model=embedding_model.model_id,
            dimension=embedding_model.dimension,
        )

    def _get_sparse_embedder(self, project_config: ProjectConfigDetailGetSchema, required: bool = True):
        sparse_embedding_model = project_config.sparse_text_model
        sparse_embedding_model_credential = project_config.sparse_text_model_credential

        if sparse_embedding_model is None:
            logger.error({"message": "Sparse Embedding Model is not configured", "org_id": self.org_id, "project_id": self.project_id})
            if required:
                raise ValueError("Sparse Embedding Model is not configured")
            return None

        if sparse_embedding_model.provider_type == "cloud" and sparse_embedding_model_credential is None:
            logger.error({"message": "Sparse Embedding Model Credential is not configured", "org_id": self.org_id, "project_id": self.project_id})
            raise ValueError("Sparse Embedding Model Credential is not configured")

        api_key = sparse_embedding_model_credential and sparse_embedding_model_credential.api_key

        return WorkflowSparseEmbedder.sparse_embedder(
            model=sparse_embedding_model.model_id,
            provider=sparse_embedding_model.provider,
            provider_type=sparse_embedding_model.provider_type,
            api_key=api_key,
        )

    def _get_reranker(self, project_config: ProjectConfigDetailGetSchema):
        """Returns None if reranking is disabled for this project."""
        if not project_config.reranker_enable:
            logger.warning({"message": "Reranker is not enabled", "org_id": self.org_id, "project_id": self.project_id})
            return None

        reranker_model = project_config.reranker_model
        reranker_model_credential = project_config.reranker_model_credential

        if reranker_model is None:
            logger.error({"message": "Reranker Model is not configured", "org_id": self.org_id, "project_id": self.project_id})
            raise ValueError("Reranker Model is not configured")

        if reranker_model.provider_type == "cloud" and reranker_model_credential is None:
            logger.error({"message": "Reranker Model Credential is not configured", "org_id": self.org_id, "project_id": self.project_id})
            raise ValueError("Reranker Model Credential is not configured")

        api_key = reranker_model_credential and reranker_model_credential.api_key

        return WorkflowReranker().reranker(
            model=reranker_model.model_id,
            provider=reranker_model.provider,
            provider_type=reranker_model.provider_type,
            api_key=api_key,
        )

    # ------------------------------------------------------------------
    # Shared chunk / scoring helpers
    # ------------------------------------------------------------------
    def _extract_qdrant_chunk_scores(self, points: list[ScoredPoint], keep_max_per_id: bool = False) -> dict[str, float]:
        scores: dict[str, float] = {}
        for point in points:
            score = point.score
            if score < Env.GTE_QDRANT_POINT_SCORE_THRESHOLD:
                continue
            payload = point.payload
            if payload is None:
                continue
            text = payload.get("text")
            chunk_id = payload.get("chunk_id")
            if text is None or chunk_id is None:
                continue
            if keep_max_per_id:
                prev = scores.get(chunk_id)
                if prev is None or score > prev:
                    scores[chunk_id] = score
            else:
                scores[chunk_id] = score
        return scores

    def _dedupe_and_sort(self, chunks: Sequence[ChunkLike]) -> list[ChunkLike]:
        seen_ids: set[str] = set()
        deduped: list[ChunkLike] = []
        for chunk in chunks:
            if chunk.chunk_id in seen_ids:
                continue
            deduped.append(chunk)
            seen_ids.add(chunk.chunk_id)
            if chunk.prev_chunk:
                seen_ids.add(chunk.prev_chunk.chunk_id)
            if chunk.next_chunk:
                seen_ids.add(chunk.next_chunk.chunk_id)
        return sorted(deduped, key=lambda x: x.point_score, reverse=True)

    async def _rerank_chunks(
        self,
        query: str,
        chunks: Sequence[ChunkLike],
        top_k: int,
        project_config: ProjectConfigDetailGetSchema,
        log_tag: str,
    ) -> list[ChunkLike]:
        if not chunks:
            raise Exception("No chunks found")

        reranker = self._get_reranker(project_config)
        if reranker is None:
            return []

        chunk_map: dict[str, ChunkLike] = {chunk.chunk_id: chunk for chunk in chunks}
        docs = [Document(page_content=c.text, metadata={"chunk_id": c.chunk_id}) for c in chunks]

        rerank_docs = await reranker.rerank(query=query, docs=docs, top_k=top_k)
        reranked = [chunk_map[doc.metadata["chunk_id"]] for doc in rerank_docs]

        deduped = self._dedupe_and_sort(reranked)
        logger.info({"message": f"[{log_tag}] Final reranked chunks", "count": len(deduped)})
        return deduped

    def _safe_serialize(self, c) -> dict:
        if hasattr(c, "model_dump"):          # Pydantic v2
            return c.model_dump(mode="json")
        elif hasattr(c, "dict"):              # Pydantic v1
            return c.dict()
        elif isinstance(c, dict):             # Already a dict
            return c
        return vars(c)                        # Fallback -- any object

    def _dedupe_metadata(self, metadata: list[dict]) -> list[dict]:
        """Collapses metadata entries collected across multiple tool calls by
        chunk_id, merging which tool(s) surfaced each chunk, and sorts by
        relevance score (point_score for main chunks, weight for vector-similar
        entries) so the UI gets a clean, ranked list rather than raw call history."""
        merged: dict[str, dict] = {}
        for entry in metadata:
            chunk_id = entry.get("chunk_id")
            if not chunk_id:
                continue
            source = entry.get("source")
            if chunk_id not in merged:
                merged[chunk_id] = {**entry, "sources": [source] if source else []}
            else:
                sources = merged[chunk_id].setdefault("sources", [])
                if source and source not in sources:
                    sources.append(source)
        for entry in merged.values():
            entry.pop("source", None)
        return sorted(
            merged.values(),
            key=lambda e: e.get("point_score") or e.get("weight") or 0,
            reverse=True,
        )

    def _format_chunks_for_agent(self, chunks: list) -> str:
        """Plain-text rendering of chunks for the LLM to reason over (not the
        structured metadata sent to the UI -- see _safe_serialize for that)."""
        if not chunks:
            return "No chunks found."
        blocks = []
        for c in chunks:
            score = getattr(c, "point_score", None) or getattr(c, "weight", 0)
            blocks.append(f"[Chunk {c.chunk_number}] (chunk_id: {c.chunk_id}, score: {score:.3f})\n{c.text}")
        return "\n\n".join(blocks)

    def _extract_content_string(self, content: Union[str, list, Any]) -> str:
        """Safely extracts a string from AIMessage content, regardless of multimodal list formats."""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            # Fallback for multimodal lists containing text dicts
            return " ".join(c if isinstance(c, str) else str(c.get("text", "")) for c in content)
        return str(content) if content else ""

    async def _stream_llm(self, llm, messages: list[BaseMessage], config: RunnableConfig) -> AIMessage:
        """Streams the model turn (so the top-level astream_events consumer gets
        live on_chat_model_stream events) and returns the accumulated message."""
        full: AIMessage | None = None
        async for chunk in llm.astream(messages, config=config):
            full = chunk if full is None else full + chunk

        if full is None:
            return AIMessage(content="")

        return full

    # ------------------------------------------------------------------
    # Nodes: supervisor / query expansion
    # ------------------------------------------------------------------
    async def _supervisor(self, state: ReActDQGState):
        try:
            query = state["query"]
            if query is None or query.strip() == "":
                raise Exception("Query is None")

            new_query = query.strip()
            top_k = state["top_k"]
            if top_k is None or top_k == 0:
                top_k = 10

            return {
                "queries": [new_query],
                "top_k": top_k,
            }
        except Exception as e:
            logger.error({"message": "Failed to supervisor", "error": str(e)})
            raise e

    async def _query_expansion(self, state: ReActDQGState):
        original_query = (state["query"] or "").strip()
        try:
            if not original_query:
                return {"queries": [original_query]}

            project_config = state["project_config"]
            llm = self._get_llm(project_config, structured_output=QueryExpansionResponse)

            prompt = QUERY_EXPANSION_PROMPT.format(query=original_query)
            response = await llm.ainvoke(prompt)
            expanded_query = self._extract_expanded_query(response)

            if not expanded_query:
                raise ValueError("Expanded query is empty")

            logger.info({
                "message": "Query expanded successfully",
                "original_query_length": len(original_query),
                "expanded_query_length": len(expanded_query),
            })
            return {"queries": [expanded_query]}
        except Exception as e:
            logger.error({"message": "Failed to query expansion", "error": str(e)})
            return {"queries": [original_query]}

    def _extract_expanded_query(self, response) -> str:
        if isinstance(response, QueryExpansionResponse):
            return response.expanded_query.strip()
        if isinstance(response, dict):
            return str(response.get("expanded_query") or "").strip()
        return str(getattr(response, "expanded_query", "") or "").strip()

    # ------------------------------------------------------------------
    # Tool factory -- builds request-scoped tools closing over query context
    # ------------------------------------------------------------------
    def _build_agent_tools(
        self,
        state: ReActDQGState,
        document_id: uuid.UUID | None,
        project_config: ProjectConfigDetailGetSchema,
        query_depth: qs.QueryDepth,
        metadata_collector: list[dict],
        chunk_cache: dict[str, ChunkLike],
        agent_extras: dict,
    ) -> list[BaseTool]:

        async def vector_search(query: str, top_k: int = 5) -> str:
            """Semantic hybrid (dense + sparse) search over the document's chunks. \
Use this first for most questions -- it finds the most relevant passages by meaning."""
            embedder = self._get_embedder(project_config)
            sparse_embedder = self._get_sparse_embedder(project_config, required=False)

            dense_emb = await embedder.aembed(query)
            sparse_emb = await sparse_embedder.embed(query) if sparse_embedder else None

            if sparse_emb is None:
                return "Error: sparse embedding is not configured for this project, cannot run vector_search."

            result: QueryResponse = await self.q_retrieval.retrieve(
                model_key=state["ep_model_key"],
                query_sparse_embedding=sparse_emb,
                query_dense_embedding=dense_emb,
                top_k=top_k,
                document_id=document_id,
            )

            chunk_scores = self._extract_qdrant_chunk_scores(result.points)
            if not chunk_scores:
                return "No relevant chunks found via vector search."

            chunks = await self._chunk_n4j.get_prev_next_chunks(
                chunk_id_scores=list(chunk_scores.items()), document_id=document_id
            )
            for c in chunks:
                chunk_cache[c.chunk_id] = c
                metadata_collector.append({"source": "vector_search", **self._safe_serialize(c)})

            return self._format_chunks_for_agent(chunks)

        async def lexical_lane_search(query: str) -> str:
            """Graph-database lookup by tags, keywords, phrases, named entities, concepts, and \
acronyms. Use this when vector_search seems to miss exact terms, specific numbers, table values, \
or named entities -- it's often stronger than pure semantic search for precise factual lookups."""
            analysis = None
            if query_depth == qs.QueryDepth.ADVANCED:
                analysis = self._lexical_engine.analyze_query(query)
                agent_extras["eq_analysis"] = analysis

            lane_edges = await self._eq_get_chunk_ids_by_lanes(analysis=analysis)
            chunk_id_scores = await self._eq_get_chunk_id_scores_by_spare_embedding_compare(
                state, query, lane_edges
            )
            agent_extras["eq_lexical_engine_chunk_ids"] = chunk_id_scores

            if not chunk_id_scores:
                return "No relevant chunks found via lexical lane search."

            top = sorted(chunk_id_scores, key=lambda x: x[1], reverse=True)[:Env.EQ_MAX_CHUNKS_COUNT]
            chunks = await self._chunk_n4j.get_prev_next_chunks(chunk_id_scores=top, document_id=document_id)
            for c in chunks:
                chunk_cache[c.chunk_id] = c
                metadata_collector.append({"source": "lexical_lane_search", **self._safe_serialize(c)})

            return self._format_chunks_for_agent(chunks)

        async def get_similar_chunks(chunk_ids: list[str]) -> str:
            """Given chunk_ids you've already retrieved via another tool, finds other chunks \
elsewhere in the document that are semantically similar -- e.g. cross-references, or repeated \
mentions of the same figure/fact in a different section."""
            if not chunk_ids:
                return "Error: no chunk_ids provided."

            chunk_id_scores = [(cid, 1.0) for cid in chunk_ids]
            vec_similar: Dict[str, ChunkVecSimilarity] = await self._chunk_n4j.get_vector_similar_chunks(
                chunk_id_scores=chunk_id_scores,
                document_id=document_id,
                gte__vector_score=Env.GTE_EDGE_VECTOR_SIMILAR_THRESHOLD,
            )

            if not vec_similar:
                return "No similar chunks found."

            lines = []
            for cid, sim in vec_similar.items():
                for vc in (sim.vector_similar_chunks or []):
                    metadata_collector.append({
                        "source": "get_similar_chunks",
                        "chunk_id": vc.chunk_id,
                        "chunk_number": vc.chunk_number,
                        "weight": vc.weight,
                        "text": vc.text,
                        "related_to_chunk_id": cid,
                    })
                    lines.append(f"[Similar to {cid}] Chunk {vc.chunk_number} (score {vc.weight:.2f}):\n{vc.text}")

            return "\n\n".join(lines) if lines else "No similar chunks found."

        async def rerank_chunks(query: str, chunk_ids: list[str]) -> str:
            """Given chunk_ids you've already retrieved from one or more prior tool calls, \
reorders them by true relevance to the query. Use this before answering whenever you've pulled \
chunks from more than one search, so you know which ones actually matter."""
            chunks = [chunk_cache[cid] for cid in chunk_ids if cid in chunk_cache]
            if not chunks:
                return "Error: none of the given chunk_ids are in the retrieved chunk cache. Call vector_search or lexical_lane_search first."

            reranked = await self._rerank_chunks(
                query=query, chunks=chunks, top_k=len(chunks), project_config=project_config, log_tag="Agent"
            )
            if not reranked:
                return "Reranker is not enabled for this project; use the chunks as originally retrieved."

            return self._format_chunks_for_agent(reranked)

        return [
            tool(vector_search),
            tool(lexical_lane_search),
            tool(get_similar_chunks),
            tool(rerank_chunks),
        ]

    # ------------------------------------------------------------------
    # Node: the ReAct agent loop
    # ------------------------------------------------------------------
    async def _agent_node(self, state: ReActDQGState, config: RunnableConfig) -> dict:
        try:
            document_id = state["document_id"]
            project_config = state["project_config"]
            query_type = state["query_type"]
            query_depth = state["query_depth"]

            queries = state.get("queries") or []
            effective_query = queries[-1] if queries else state["query"]

            metadata_collector: list[dict] = []
            chunk_cache: dict[str, ChunkLike] = {}
            agent_extras: dict = {"eq_analysis": None, "eq_lexical_engine_chunk_ids": None}

            tools = self._build_agent_tools(
                state=state,
                document_id=document_id,
                project_config=project_config,
                query_depth=query_depth,
                metadata_collector=metadata_collector,
                chunk_cache=chunk_cache,
                agent_extras=agent_extras,
            )
            tool_map = {t.name: t for t in tools}

            base_llm = self._get_llm(project_config)
            llm_with_tools = base_llm.bind_tools(tools)

            system_prompt = AGENT_SYSTEM_PROMPT.format(
                query_type=getattr(query_type, "value", query_type),
                query_depth=getattr(query_depth, "value", query_depth),
            )
            messages: list[BaseMessage] = [SystemMessage(content=system_prompt), HumanMessage(content=effective_query)]

            final_text: str | None = None

            for _ in range(MAX_AGENT_TURNS):
                response = await self._stream_llm(llm_with_tools, messages, config)
                messages.append(response)

                if not response.tool_calls:
                    final_text = self._extract_content_string(response.content)
                    break

                for tool_call in response.tool_calls:
                    tool_obj = tool_map.get(tool_call["name"])
                    if tool_obj is None:
                        tool_result = f"Error: unknown tool '{tool_call['name']}'"
                    else:
                        try:
                            tool_result = await tool_obj.ainvoke(tool_call["args"], config=config)
                        except Exception as te:
                            logger.error({"message": "Tool execution failed", "tool": tool_call["name"], "error": str(te)})
                            tool_result = f"Error executing {tool_call['name']}: {te}"

                    messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call["id"]))

            if final_text is None:
                # Hit MAX_AGENT_TURNS without a plain-text answer -- force one, no tools bound,
                # so we never return an empty answer just because the agent kept calling tools.
                messages.append(HumanMessage(
                    content="You've reached the tool-call limit. Provide your best final answer now, "
                            "based on the information already gathered."
                ))
                forced = await self._stream_llm(base_llm, messages, config)
                extracted_text = self._extract_content_string(forced.content)
                final_text = extracted_text if extracted_text.strip() else "I wasn't able to find a definitive answer in the document."

            deduped_metadata = self._dedupe_metadata(metadata_collector)

            return {
                "answer": final_text,
                "metadata": deduped_metadata,
                "eq_analysis": agent_extras["eq_analysis"],
                "eq_lexical_engine_chunk_ids": agent_extras["eq_lexical_engine_chunk_ids"],
            }
        except Exception as e:
            logger.error({"message": "Failed in agent node", "error": str(e)})
            raise e

    # ------------------------------------------------------------------
    # Lexical-lane helpers (used by the lexical_lane_search tool)
    # ------------------------------------------------------------------
    async def _eq_get_chunk_ids_by_lanes(
        self,
        analysis: QueryAnalysis | None = None,  # None = standard, provided = advanced
    ) -> dict[str, List[N4jCommonEdgeChunksSchema]]:
        try:
            gte_lane_weight_threshold = Env.EQ_GTE_LANE_WEIGHT_THRESHOLD

            if analysis is not None:
                lanes = [lane for lane, _ in analysis.lane_priority[:Env.EQ_MAX_LANE_COUNT]]
            else:
                lanes = [
                    GNeo4jEdges.HAS_TAG,
                    GNeo4jEdges.HAS_KEYWORD,
                    GNeo4jEdges.HAS_PHRASE,
                    GNeo4jEdges.HAS_ENTITY,
                    GNeo4jEdges.HAS_CONCEPT,
                    GNeo4jEdges.HAS_ACRONYM
                ]

            lane_edges: dict[str, List[N4jCommonEdgeChunksSchema]] = {}

            for lane in lanes:
                try:
                    res = await self._n4j_mapping_client.get_mapping_for_org_project(
                        edge_type=lane,
                        is_all=True,
                    )

                    filtered: List[N4jCommonEdgeChunksSchema] = []
                    for node in res:
                        if not node.chunks_ids:
                            continue

                        valid_chunks = [
                            chunk for chunk in node.chunks_ids
                            if chunk.weight >= gte_lane_weight_threshold
                        ]

                        if not valid_chunks:
                            continue

                        filtered.append(
                            N4jCommonEdgeChunksSchema(
                                id=node.id,
                                type=node.type,
                                value=node.value,
                                frequency=node.frequency,
                                chunks_ids=valid_chunks,
                            )
                        )

                    lane_edges[lane] = filtered

                except Exception as e:
                    logger.error({"message": "Failed to get chunk ids for lane", "lane": lane, "error": str(e)})
                    lane_edges[lane] = []

            return lane_edges

        except Exception as e:
            logger.error({"message": "Failed to eq_get_chunk_ids_by_lanes", "error": str(e)})
            raise e

    async def _eq_get_chunk_id_scores_by_spare_embedding_compare(
        self,
        state: ReActDQGState,
        query: str,
        lanes: dict[str, List[N4jCommonEdgeChunksSchema]],
        normalized_query_per_lane: dict[str, str] | None = None,
    ) -> set[Tuple[str, float]]:
        try:
            project_config = state["project_config"]

            sparse_embedder = self._get_sparse_embedder(project_config, required=False)
            if sparse_embedder is None:
                return set()

            embedder = self._get_embedder(project_config)
            max_chunk_count = Env.EQ_MAX_LANE_CHUNKS_COUNT

            chunk_scores: dict[str, float] = {}

            for lane, nodes in lanes.items():
                if not nodes:
                    continue

                normalized_query = (
                    normalized_query_per_lane.get(lane)
                    if normalized_query_per_lane
                    else self._lexical_engine.normalize_query_for_lane(query=query, edge_type=lane)
                ) or self._lexical_engine.normalize_query_for_lane(query=query, edge_type=lane)

                normalized_node_values: List[str] = [
                    self._lexical_engine.normalize_node_value(value=node.value, edge_type=lane)
                    for node in nodes
                ]

                all_texts = [normalized_query] + normalized_node_values

                if lane in SPARSE_LANES:
                    embeddings: list[SparseEmbedding] = await sparse_embedder.embed_batch(all_texts)
                    query_emb = embeddings[0]
                    node_embs = embeddings[1:]

                    similarities = [
                        self._sparse_dot_score(query_emb, node_emb)
                        for node_emb in node_embs
                    ]

                else:
                    dense_embeddings: list[list[float]] = await embedder.aembed_batch(all_texts)
                    query_emb_dense = dense_embeddings[0]
                    node_embs_dense = dense_embeddings[1:]

                    similarities = [
                        self._cosine_score(query_emb_dense, node_emb)
                        for node_emb in node_embs_dense
                    ]

                for node, similarity in zip(nodes, similarities):
                    if similarity <= 0 or not node.chunks_ids:
                        continue

                    for chunk in node.chunks_ids:
                        combined_score = similarity * chunk.weight
                        if combined_score > chunk_scores.get(chunk.chunk_id, 0):
                            chunk_scores[chunk.chunk_id] = combined_score

            ranked = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
            return set(ranked[:max_chunk_count])

        except Exception as e:
            logger.error({"message": "Failed to eq_get_chunk_id_scores_by_spare_embedding_compare", "error": str(e)})
            raise e

    def _cosine_score(self, a: list[float], b: list[float]) -> float:
        import numpy as np
        a_arr = np.array(a)
        b_arr = np.array(b)
        denom = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        if denom == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / denom)

    def _sparse_dot_score(self, a: SparseEmbedding, b: SparseEmbedding) -> float:
        """Dot product between two sparse embeddings (unbounded, exact-token-overlap score)."""
        b_map = dict(zip(b.indices, b.values))
        score = sum(
            a_val * b_map[idx]
            for idx, a_val in zip(a.indices, a.values)
            if idx in b_map
        )
        return float(score)
