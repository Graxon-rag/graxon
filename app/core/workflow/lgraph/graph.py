from ..schemas.provider_schema import ProviderSchema, QueryProviderSchema
from .document_inject_graph import DocumentInjectGraph, DIGState
from app.core.schemas.document_schema import DocumentGetSchema
from .document_query_graph import DocumentQueryGraph, DQGState
from app.utils.logger import logger
from typing import Optional
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

            request_id = str(uuid.uuid4())
            graph = DocumentInjectGraph(org_id=self.org_id, project_id=self.project_id, document_id=document.id, document_readable_id=document.readable_id)
            workflow = graph.build_graph()
            initial_state: DIGState = {
                "request_id": request_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
                "document_id": document.id,
                "document": document,
                "providers": providers,
                "temp_path": None,
                "file_path": None,
                "chunk_size": Env.CHUNK_SIZE,
                "chunk_overlap": Env.CHUNK_OVERLAP,
                "chunks": None,
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

    async def query_documents(self, providers: QueryProviderSchema, query: str, document_id: Optional[uuid.UUID] = None, top_k: int = 10):
        try:
            print("Query:", query)
            print("Providers:", providers.model_dump(mode="json"))
            request_id = str(uuid.uuid4())

            graph = DocumentQueryGraph(org_id=self.org_id, project_id=self.project_id)
            workflow = graph.build_graph()
            if workflow is None:
                raise Exception("Workflow is None")

            initial_state: DQGState = {
                "request_id": request_id,
                "org_id": self.org_id,
                "project_id": self.project_id,
                "providers": providers,
                "model_key": None,
                "query": query,
                "queries": [query],
                "top_k": top_k,
                "document_id": document_id,
                "query_dense_embedding": None,
                "query_sparse_embedding": None,
                "answer": None
            }
            result = await workflow.ainvoke(initial_state)
            return result.get("answer")
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e
