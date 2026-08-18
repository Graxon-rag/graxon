from ..services.chunk_service import ChunkService
from ..schemas import chunk_schema as cs
from app.utils.logger import logger
from typing import List
import uuid


class ChunkHandler:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self._service = ChunkService(org_id=org_id, project_id=project_id, document_id=document_id)
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id

    async def list(self, params: cs.ChunkQueryParams) -> cs.ChunkListSchema:
        try:
            return await self._service.list(params=params)
        except Exception as e:
            logger.error({"message": "Failed to list chunks", "error": str(e)})
            raise e

    async def get(self, id: uuid.UUID) -> cs.ChunkGetSchema | None:
        try:
            return await self._service.get(id=id)
        except Exception as e:
            logger.error({"message": "Failed to get chunk", "error": str(e)})
            raise e

    async def get_all_chunk_id_and_number(self) -> List[tuple[str, int]]:
        try:
            return await self._service.get_all_chunk_id_and_number()
        except Exception as e:
            logger.error({"message": "Failed to get chunk", "error": str(e)})
            raise e
