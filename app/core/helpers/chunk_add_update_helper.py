from ..schemas.project_config_schema import ProjectConfigDetailGetSchema
from ..common.providers.sparse_embedder import SparseEmbedderProvider
from fastembed.sparse.sparse_embedding_base import SparseEmbedding
from ..common.providers.embedder import EmbeddingProvider
from ..libs.embedding_lib import EmbeddingLib
from ..qdrant.inject import QdrantInjector
from ..schemas import chunk_schema as cs
from app.utils.logger import logger
from ..neo4j.chunk import GN4jChunk
import uuid


class ChunkVectorDBHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.qdrant_injector = QdrantInjector(org_id=org_id, project_id=project_id)
        self.neo4j_injector = GN4jChunk(org_id=org_id, project_id=project_id)

    async def add_chunk(self, doc_id: uuid.UUID, pc: ProjectConfigDetailGetSchema, c: cs.ChunkCreateSchema) -> bool:
        try:
            embedder_provider = pc.embedding_model
            if embedder_provider is None:
                raise Exception("Embedder provider not found")
            ep_model_key = EmbeddingLib.get_model_key(embedder_provider.provider.value, embedder_provider.dimension)
            embedder = EmbeddingProvider.get(pc)
            embeddings = await embedder.aembed(c.text)
            sparse_embeddings: SparseEmbedding | None = None
            sparse_embedder = SparseEmbedderProvider.get(pc)
            if sparse_embedder is not None:
                sparse_embeddings = await sparse_embedder.embed(c.text)
            if sparse_embeddings is not None:
                chunk_sparse_embedding = cs.ChunkSparseEmbedding(chunk_id=c.chunk_id, embedding=sparse_embeddings, chunk_number=c.chunk_number)
            else:
                chunk_sparse_embedding = None
            await self.qdrant_injector.add_chunk(model_key=ep_model_key, document_id=doc_id, chunk=c, chunk_embedding=cs.ChunkEmbedding(chunk_id=c.chunk_id, embedding=embeddings, chunk_number=c.chunk_number), chunk_sparse_embedding=chunk_sparse_embedding)
            return True
        except Exception as e:
            logger.error({"message": "Failed to add new chunk", "error": str(e)})
            raise e

    async def update_chunk(self, doc_id: uuid.UUID, pc: ProjectConfigDetailGetSchema, chunk: cs.Chunk) -> bool:
        try:
            embedder_provider = pc.embedding_model
            if embedder_provider is None:
                raise Exception("Embedder provider not found")
            ep_model_key = EmbeddingLib.get_model_key(embedder_provider.provider.value, embedder_provider.dimension)
            embedder = EmbeddingProvider.get(pc)
            embeddings = await embedder.aembed(chunk.text)
            sparse_embeddings: SparseEmbedding | None = None
            sparse_embedder = SparseEmbedderProvider.get(pc)
            if sparse_embedder is not None:
                sparse_embeddings = await sparse_embedder.embed(chunk.text)
            if sparse_embeddings is not None:
                chunk_sparse_embedding = cs.ChunkSparseEmbedding(chunk_id=chunk.chunk_id, embedding=sparse_embeddings, chunk_number=chunk.chunk_number)
            else:
                chunk_sparse_embedding = None
            await self.qdrant_injector.add_chunk(model_key=ep_model_key, document_id=doc_id, chunk=chunk, chunk_embedding=cs.ChunkEmbedding(chunk_id=chunk.chunk_id, embedding=embeddings, chunk_number=chunk.chunk_number), chunk_sparse_embedding=chunk_sparse_embedding)
            return True
        except Exception as e:
            logger.error({"message": "Failed to update chunk", "error": str(e)})
            raise e


class ChunkGraphDBHelper:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.org_id = org_id
        self.project_id = project_id
        self.neo4j_injector = GN4jChunk(org_id=org_id, project_id=project_id)

    async def add_chunk(self, doc_id: uuid.UUID, document_readable_id: str, c: cs.ChunkCreateSchema) -> bool:
        try:
            await self.neo4j_injector.create_multiple(document_id=doc_id, document_readable_id=document_readable_id, chunks=[c])
            return True
        except Exception as e:
            logger.error({"message": "Failed to add new chunk", "error": str(e)})
            raise e

    async def update_chunk(self, doc_id: uuid.UUID, chunk: cs.Chunk) -> bool:
        try:
            await self.neo4j_injector.update(document_id=doc_id, chunk=chunk)
            return True
        except Exception as e:
            logger.error({"message": "Failed to update chunk", "error": str(e)})
            raise e
