from ..helpers.chunk_add_update_helper import ChunkVectorDBHelper, ChunkGraphDBHelper
from .project_config_service import ProjectConfigService
from .document_service import DocumentService
from ..schemas import chunk_schema as cs
from ..repos.chunk_repo import ChunkRepo
from app.utils.logger import logger
from ..libs.id import IDLibs
from typing import List
import uuid


class ChunkService:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self._repo = ChunkRepo(org_id=org_id, project_id=project_id, document_id=document_id)
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id
        self.document_service = DocumentService(org_id=org_id, project_id=project_id)
        self.project_config_service = ProjectConfigService(org_id=org_id, project_id=project_id)
        self.chunk_vector_db_helper = ChunkVectorDBHelper(org_id=org_id, project_id=project_id)
        self.chunk_graph_db_helper = ChunkGraphDBHelper(org_id=org_id, project_id=project_id)

    async def create(self, chunk: cs.ChunkCreateSchema) -> bool:
        try:
            return await self._repo.create(chunk=chunk)
        except Exception as e:
            logger.error({"message": "Failed to create chunk", "error": str(e)})
            raise e

    async def add(self, c: cs.ChunkAddParams) -> bool:
        try:
            document = await self.document_service.get(self.document_id)
            if document is None:
                logger.error({"message": "Failed to add chunk", "error": "No document found"})
                raise Exception("No document found")
            last_chunk = await self._repo.get_last_chunk()
            if last_chunk is None:
                logger.error({"message": "Failed to add chunk", "error": "No last chunk found"})
                raise Exception("No last chunk found")

            project_config = await self.project_config_service.get_with_details_by_project()
            if project_config is None:
                logger.error({"message": "Failed to add chunk", "error": "No project config found"})
                raise Exception("No project config found")

            new_chunk_number = last_chunk.chunk_number + 1
            chunk = cs.ChunkCreateSchema(
                chunk_id=IDLibs.generate_chunk_id(document_id=str(self.document_id), chunk_number=new_chunk_number),
                chunk_number=new_chunk_number,
                text=c.text,
                metadata=c.metadata,
                file_chunk_number=c.file_chunk_number or last_chunk.file_chunk_number
            )
            await self.create(chunk)
            await self.chunk_vector_db_helper.add_chunk(doc_id=self.document_id, pc=project_config, c=chunk)
            return await self.chunk_graph_db_helper.add_chunk(doc_id=self.document_id, document_readable_id=document.readable_id, c=chunk)
        except Exception as e:
            logger.error({"message": "Failed to add chunk", "error": str(e)})
            raise e

    async def update(self, u: cs.ChunkUpdateParams) -> bool:
        try:
            project_config = await self.project_config_service.get_with_details_by_project()
            if project_config is None:
                logger.error({"message": "Failed to add chunk", "error": "No project config found"})
                raise Exception("No project config found")
            chunk = await self.get(id=u.id)
            if chunk is None:
                raise Exception(f"Chunk with id {u.id} not found")
            await self._repo.update(u=u)

            # Update chunk vector
            chunk.text = u.text

            await self.chunk_vector_db_helper.update_chunk(doc_id=self.document_id, pc=project_config, chunk=chunk)
            return await self.chunk_graph_db_helper.update_chunk(doc_id=self.document_id, chunk=chunk)
        except Exception as e:
            logger.error({"message": "Failed to update chunk", "error": str(e)})
            raise e

    async def create_multiple(self, chunks: list[cs.ChunkCreateSchema]) -> bool:
        try:
            return await self._repo.create_multiple(chunks=chunks)
        except Exception as e:
            logger.error({"message": "Failed to create chunks", "error": str(e)})
            raise e

    async def list(self, params: cs.ChunkQueryParams) -> cs.ChunkListSchema:
        try:
            return await self._repo.list(params=params)
        except Exception as e:
            logger.error({"message": "Failed to list chunks", "error": str(e)})
            raise e

    async def get(self, id: uuid.UUID) -> cs.ChunkGetSchema | None:
        try:
            return await self._repo.get(id=id)
        except Exception as e:
            logger.error({"message": "Failed to get chunk", "error": str(e)})
            raise e

    async def get_all_chunk_id_and_number(self) -> List[tuple[str, int]]:
        try:
            return await self._repo.get_all_chunk_id_and_number()
        except Exception as e:
            logger.error({"message": "Failed to get chunk", "error": str(e)})
            raise e
