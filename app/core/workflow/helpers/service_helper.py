from ...services.project_service import ProjectService
from ...services.model_credential_service import ModelCredentialService
from ...services.reranker_service import ReRankerService
from ...services.embedding_model_service import EmbeddingModelService
from ...services.sparse_text_model_service import SparseTextModelService
from ...services.llm_model_service import LLMModelService
from ...services.document_service import DocumentService

from ...schemas.project_schema import ProjectGetSchema
from ...schemas.document_schema import DocumentGetSchema
from ...schemas.model_credential_schema import ModelCredentialGetSchema
from ...schemas.reranker_schema import ReRankerGetSchema
from ...schemas.embedding_model_schema import EmbeddingModelGetSchema
from ...schemas.sparse_text_model_schema import SparseTextModelGetSchema
from ...schemas.llm_model_schema import LLMModelGetSchema

from app.utils.logger import logger
import uuid


class DocumentServiceHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id
        self._service = DocumentService(org_id=self.org_id, project_id=self.project_id)

    async def get_document(self) -> DocumentGetSchema:
        try:
            document = await self._service.get(self.document_id)
            if not document:
                raise Exception(f"Document with id {self.document_id} not found")
            return document
        except Exception as e:
            logger.error({"message": "Failed to get document", "error": str(e)})
            raise e


class RerankerServiceHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self._service = ReRankerService(org_id=self.org_id)

    async def get_reranker(self, reranker_id: uuid.UUID) -> ReRankerGetSchema:
        try:
            reranker = await self._service.get_reranker(reranker_id)
            if not reranker:
                raise Exception(f"Reranker with id {reranker_id} not found")
            return reranker
        except Exception as e:
            logger.error({"message": "Failed to get reranker", "error": str(e)})
            raise e


class LLMModelServiceHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self._service = LLMModelService(org_id=self.org_id)

    async def get_llm_model(self, llm_model_id: uuid.UUID) -> LLMModelGetSchema:
        try:
            llm_model = await self._service.get_llm_model(llm_model_id)
            if not llm_model:
                raise Exception(f"LLM Model with id {llm_model_id} not found")
            return llm_model
        except Exception as e:
            logger.error({"message": "Failed to get LLM Model", "error": str(e)})
            raise e


class EmbeddingModelServiceHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self._service = EmbeddingModelService(org_id=self.org_id)

    async def get_embedding_model(self, embedding_model_id: uuid.UUID) -> EmbeddingModelGetSchema:
        try:
            embedding_model = await self._service.get_embedding_model(embedding_model_id)
            if not embedding_model:
                raise Exception(f"Embedding Model with id {embedding_model_id} not found")
            return embedding_model
        except Exception as e:
            logger.error({"message": "Failed to get Embedding Model", "error": str(e)})
            raise e


class SparseTextModelServiceHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self._service = SparseTextModelService(org_id=self.org_id)

    async def get_sparse_model(self, sparse_model_id: uuid.UUID) -> SparseTextModelGetSchema:
        try:
            sparse_model = await self._service.get_sparse_text_model(sparse_model_id)
            if not sparse_model:
                raise Exception(f"Sparse Model with id {sparse_model_id} not found")
            return sparse_model
        except Exception as e:
            logger.error({"message": "Failed to get Sparse Model", "error": str(e)})
            raise e


class ModelCredentialServiceHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self._service = ModelCredentialService(org_id=self.org_id)

    async def get_model_credential(self, model_credential_id: uuid.UUID) -> ModelCredentialGetSchema:
        try:
            # is_external_call=False because we don't want to hash the api key
            model_credential = await self._service.get_model_credential(model_credential_id, is_external_call=False)
            if not model_credential:
                raise Exception(f"Model credential with id {model_credential_id} not found")
            return model_credential
        except Exception as e:
            logger.error({"message": "Failed to get model credential", "error": str(e)})
            raise e


class ProjectServiceHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self._service = ProjectService(org_id=self.org_id)

    async def get_project(self) -> ProjectGetSchema:
        try:
            project = await self._service.get(self.project_id)
            if not project:
                raise Exception(f"Project with id {self.project_id} not found")
            return project
        except Exception as e:
            logger.error({"message": "Failed to get project", "error": str(e)})
            raise e
