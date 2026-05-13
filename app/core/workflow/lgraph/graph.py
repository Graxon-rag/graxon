from ..schemas.provider_schema import ProviderSchema, QueryProviderSchema
from .document_inject_graph import DocumentInjectGraph, DIGState
from app.core.schemas.document_schema import DocumentGetSchema
from .document_query_graph import DocumentQueryGraph, DQGState
from .prompts.answer_prompt import DEFAULT_ANSWER_RESPONSE
from app.core.schemas.query_schema import GQuery
from app.utils.logger import logger
from app.config.env import Env
import uuid


class Graph:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id

    async def inject_document(self, document: DocumentGetSchema, providers: ProviderSchema):
        try:
            print("Document:", document.model_dump(mode="json"))
            print("Providers:", providers.model_dump(mode="json"))
            embedder_provider = providers.embedding.provider.value  # Use .value because it's a enum
            dimension = providers.embedding.dimension
            ep_model_key = self._get_model_key(embedder_provider, dimension)

            request_id = str(uuid.uuid4())
            graph = DocumentInjectGraph(org_id=self.org_id, project_id=self.project_id, document_id=document.id, document_readable_id=document.readable_id)
            workflow = graph.build_graph()
            initial_state: DIGState = {
                "request_id": request_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
                "document_id": document.id,
                "ep_model_key": ep_model_key,
                "document": document,
                "providers": providers,
                "temp_path": None,
                "file_path": None,
                "chunk_size": Env.CHUNK_SIZE,
                "chunk_overlap": Env.CHUNK_OVERLAP,
                "chunks": None,
                "tags": [],
                "chunk_tag_results": [],
                "lexical_engine_data": None,
                "chunks_embeddings": [],
                "chunks_sparse_embeddings": []
            }

            if workflow is None:
                raise Exception("Workflow is None")

            temp_path = None

            try:
                result = await workflow.ainvoke(initial_state)
                temp_path = result.get("temp_path")
                return result
            except Exception as e:
                logger.error({"message": "Failed to inject document", "error": str(e)})
                raise e
            finally:
                # Delete temp folder
                import shutil
                if temp_path:
                    shutil.rmtree(temp_path, ignore_errors=True)
                    logger.info({"message": "Deleted temp folder", "path": temp_path})

        except Exception as e:
            logger.error({"message": "Failed to inject document", "error": str(e)})
            raise e

    async def query_documents(self, providers: QueryProviderSchema, query: GQuery):
        try:
            print("Query:", query)
            print("Providers:", providers.model_dump(mode="json"))
            request_id = str(uuid.uuid4())
            embedder_provider = providers.embedding.provider.value  # Use .value because it's a enum
            dimension = providers.embedding.dimension
            ep_model_key = self._get_model_key(embedder_provider, dimension)

            graph = DocumentQueryGraph(org_id=self.org_id, project_id=self.project_id)
            workflow = graph.build_graph()
            if workflow is None:
                raise Exception("Workflow is None")

            initial_state: DQGState = {
                "request_id": request_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
                "providers": providers,
                "model_key": ep_model_key,
                "query": query.query,
                "queries": [query.query],
                "top_k": query.top_k,
                "query_type": query.query_type,
                "query_depth": query.query_depth,
                "document_id": query.document_id,
                "points": None,
                "chunks": [],
                "reranked_chunks": [],
                "query_dense_embedding": None,
                "query_sparse_embedding": None,
                "answer": None
            }
            result = await workflow.ainvoke(initial_state)
            answer = result.get("answer") or DEFAULT_ANSWER_RESPONSE
            reranked_chunks = result.get("reranked_chunks")
            metadata = [self._safe_serialize(c) for c in reranked_chunks or []]
            return {"answer": answer, "query": query.query, "metadata": metadata}
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            return DEFAULT_ANSWER_RESPONSE

    def _get_model_key(self, provider: str, dimension: int) -> str:
        return f"{provider}_{dimension}"

    def _safe_serialize(self, c):
        if hasattr(c, "model_dump"):          # Pydantic v2
            return c.model_dump(mode="json")
        elif hasattr(c, "dict"):              # Pydantic v1
            return c.dict()
        elif isinstance(c, dict):             # Already a dict
            return c
        else:                                 # Fallback — any object
            return vars(c)
