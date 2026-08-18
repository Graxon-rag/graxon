from app.utils.response_util import success_response, error_response
from fastapi import HTTPException, APIRouter, Depends
from ..schemas.chunk_schema import ChunkQueryParams
from ..handlers.chunk_handler import ChunkHandler
from app.utils.logger import logger
from starlette import status
import uuid

router = APIRouter(
    tags=["Chunks"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{org_id}/{project_id}/{document_id}/chunks/list")
async def list_chunks(org_id: str, project_id: str, document_id: str, params: ChunkQueryParams = Depends()):
    try:
        handler = ChunkHandler(org_id=org_id, project_id=uuid.UUID(project_id), document_id=uuid.UUID(document_id))
        result = await handler.list(params)
        if not result:
            logger.error({"message": "Failed to list chunks", "result": result})
            return error_response("Failed to list chunks", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to list chunks", "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{org_id}/{project_id}/{document_id}/chunks/get/{chunk_id}")
async def get_chunk(org_id: str, project_id: str, document_id: str, chunk_id: uuid.UUID):
    try:
        handler = ChunkHandler(org_id=org_id, project_id=uuid.UUID(project_id), document_id=uuid.UUID(document_id))
        result = await handler.get(chunk_id)
        if not result:
            logger.error({"message": "Failed to get chunk", "result": result})
            return error_response("Failed to get chunk", status.HTTP_404_NOT_FOUND)
        return success_response(data=result.model_dump(mode="json"))
    except Exception as e:
        logger.error({"message": "Failed to get chunk", "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
