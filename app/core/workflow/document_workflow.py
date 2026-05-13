from .schemas.provider_schema import ProviderSchema, LLMProviderSchema, EmbeddingProviderSchema, SparseModelProviderSchema, RerankerProviderSchema, QueryProviderSchema
from app.core.schemas.document_schema import DocumentGetSchema, DocumentStatus
from .helpers.service_helper import (
    LLMModelServiceHelper,
    EmbeddingModelServiceHelper,
    SparseTextModelServiceHelper,
    RerankerServiceHelper,
    ProjectServiceHelper,
    ModelCredentialServiceHelper,
    DocumentServiceHelper
)
from .helpers.model_provider_helper import ModelProviderHelper
from ..schemas.query_schema import GQuery
from app.utils.logger import logger
from .lgraph.graph import Graph
import uuid


class DocumentWorkflow:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.graph = Graph(org_id=self.org_id, project_id=self.project_id)

    async def process(self, document: DocumentGetSchema):
        try:
            await DocumentServiceHelper(self.org_id, self.project_id, document.id).update_document_status(document.id, DocumentStatus.PROCESSING)
            providers = await self._get_providers(document.id, document.readable_id)
            result = await self.graph.inject_document(document, providers)
            await DocumentServiceHelper(self.org_id, self.project_id, document.id).update_document_status(document.id, DocumentStatus.PROCESSED)
            return result
        except Exception as e:
            logger.error({"message": "Failed to process document", "error": str(e)})
            await DocumentServiceHelper(self.org_id, self.project_id, document.id).update_document_status(document.id, DocumentStatus.FAILED)
            raise e

    async def query(self, query: GQuery):
        try:
            providers = await self._get_query_providers()
            return await self.graph.query_documents(providers, query)
        except Exception as e:
            logger.error({"message": "Failed to query", "error": str(e)})
            raise e

    async def _get_query_providers(self) -> QueryProviderSchema:
        try:
            project = await ProjectServiceHelper(self.org_id, self.project_id).get_project()
            if project is None:
                raise Exception(f"Project with id {self.project_id} not found")

            llm_model_id = project.llm_model_id
            embedding_model_id = project.embedding_model_id
            sparse_text_model_id = project.sparse_text_model_id
            reranker_model_id = project.reranker_model_id
            llm_model_credential_id = project.llm_model_credential_id
            embedding_model_credential_id = project.embedding_model_credential_id

            llm_model = await LLMModelServiceHelper(self.org_id, self.project_id).get_llm_model(llm_model_id)
            embedding_model = await EmbeddingModelServiceHelper(self.org_id, self.project_id).get_embedding_model(embedding_model_id)
            sparse_text_model = await SparseTextModelServiceHelper(self.org_id, self.project_id).get_sparse_model(sparse_text_model_id)
            reranker = await RerankerServiceHelper(self.org_id, self.project_id).get_reranker(reranker_model_id)
            llm_model_credential = await ModelCredentialServiceHelper(self.org_id, self.project_id).get_model_credential(llm_model_credential_id)
            embedding_model_credential = await ModelCredentialServiceHelper(self.org_id, self.project_id).get_model_credential(embedding_model_credential_id)

            if llm_model is None:
                raise Exception(f"LLM model with id {llm_model_id} not found")
            if embedding_model is None:
                raise Exception(f"Embedding model with id {embedding_model_id} not found")
            if sparse_text_model is None:
                raise Exception(f"Sparse text model with id {sparse_text_model_id} not found")
            if reranker is None:
                raise Exception(f"Reranker model with id {reranker_model_id} not found")
            if llm_model_credential is None:
                raise Exception(f"LLM model credential with id {llm_model_credential_id} not found")
            if embedding_model_credential is None:
                raise Exception(f"Embedding model credential with id {embedding_model_credential_id} not found")

            if llm_model.provider != llm_model_credential.provider:
                raise Exception(f"LLM model provider {llm_model.provider} does not match with LLM model credential provider {llm_model_credential.provider}")

            if embedding_model.provider != embedding_model_credential.provider:
                raise Exception(f"Embedding model provider {embedding_model.provider} does not match with embedding model credential provider {embedding_model_credential.provider}")

            llm_model_provider = ModelProviderHelper.get_llm_model_provider(llm_model.provider)
            embedding_model_provider = ModelProviderHelper.get_embedding_model_provider(embedding_model.provider)

            return QueryProviderSchema(
                org_id=self.org_id,
                project_id=self.project_id,
                llm=LLMProviderSchema(
                    provider=llm_model_provider,
                    api_key=llm_model_credential.api_key,
                    model=llm_model.model_id,
                ),
                embedding=EmbeddingProviderSchema(
                    provider=embedding_model_provider,
                    api_key=embedding_model_credential.api_key,
                    model=embedding_model.model_id,
                    dimension=embedding_model.dimension,
                ),
                sparse_model=SparseModelProviderSchema(
                    provider=sparse_text_model.provider,
                    model=sparse_text_model.model,
                ),
                reranker=RerankerProviderSchema(
                    provider=reranker.provider,
                    model=reranker.model,
                ),
            )

        except Exception as e:
            logger.error({"message": "Failed to get query providers", "error": str(e)})
            raise e

    async def _get_providers(self, document_id: uuid.UUID, document_readable_id: str) -> ProviderSchema:
        try:
            project = await ProjectServiceHelper(self.org_id, self.project_id).get_project()
            if project is None:
                raise Exception(f"Project with id {self.project_id} not found")

            llm_model_id = project.llm_model_id
            embedding_model_id = project.embedding_model_id
            sparse_text_model_id = project.sparse_text_model_id
            reranker_model_id = project.reranker_model_id
            llm_model_credential_id = project.llm_model_credential_id
            embedding_model_credential_id = project.embedding_model_credential_id

            llm_model = await LLMModelServiceHelper(self.org_id, self.project_id).get_llm_model(llm_model_id)
            embedding_model = await EmbeddingModelServiceHelper(self.org_id, self.project_id).get_embedding_model(embedding_model_id)
            sparse_text_model = await SparseTextModelServiceHelper(self.org_id, self.project_id).get_sparse_model(sparse_text_model_id)
            reranker = await RerankerServiceHelper(self.org_id, self.project_id).get_reranker(reranker_model_id)
            llm_model_credential = await ModelCredentialServiceHelper(self.org_id, self.project_id).get_model_credential(llm_model_credential_id)
            embedding_model_credential = await ModelCredentialServiceHelper(self.org_id, self.project_id).get_model_credential(embedding_model_credential_id)

            if llm_model is None:
                raise Exception(f"LLM model with id {llm_model_id} not found")
            if embedding_model is None:
                raise Exception(f"Embedding model with id {embedding_model_id} not found")
            if sparse_text_model is None:
                raise Exception(f"Sparse text model with id {sparse_text_model_id} not found")
            if reranker is None:
                raise Exception(f"Reranker model with id {reranker_model_id} not found")
            if llm_model_credential is None:
                raise Exception(f"LLM model credential with id {llm_model_credential_id} not found")
            if embedding_model_credential is None:
                raise Exception(f"Embedding model credential with id {embedding_model_credential_id} not found")

            if llm_model.provider != llm_model_credential.provider:
                raise Exception(f"LLM model provider {llm_model.provider} does not match with LLM model credential provider {llm_model_credential.provider}")

            if embedding_model.provider != embedding_model_credential.provider:
                raise Exception(f"Embedding model provider {embedding_model.provider} does not match with embedding model credential provider {embedding_model_credential.provider}")

            llm_model_provider = ModelProviderHelper.get_llm_model_provider(llm_model.provider)
            embedding_model_provider = ModelProviderHelper.get_embedding_model_provider(embedding_model.provider)

            return ProviderSchema(
                org_id=self.org_id,
                project_id=self.project_id,
                document_id=document_id,
                document_readable_id=document_readable_id,
                llm=LLMProviderSchema(
                    provider=llm_model_provider,
                    api_key=llm_model_credential.api_key,
                    model=llm_model.model_id,
                ),
                embedding=EmbeddingProviderSchema(
                    provider=embedding_model_provider,
                    api_key=embedding_model_credential.api_key,
                    model=embedding_model.model_id,
                    dimension=embedding_model.dimension,
                ),
                sparse_model=SparseModelProviderSchema(
                    provider=sparse_text_model.provider,
                    model=sparse_text_model.model,
                ),
                reranker=RerankerProviderSchema(
                    provider=reranker.provider,
                    model=reranker.model,
                ),
            )
        except Exception as e:
            logger.error({"message": "Failed to get providers", "error": str(e)})
            raise e
