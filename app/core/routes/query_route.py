from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from app.utils.response_util import success_response, error_response
from fastapi import HTTPException, APIRouter, Query, Body
from ..schemas.query_schema import QueryType
from ..handlers.query_handler import QueryHandler
from app.utils.logger import logger
from typing import Optional
import uuid


router = APIRouter(
    tags=["Query"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.get("/{org_id}/projects/{project_id}")
async def query(org_id: str, project_id: uuid.UUID, query: str = Query(..., description="Query text"), document_id: Optional[uuid.UUID] = Query(
        default=None,
        description="Optional document id"
    ),
    top_k: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of results"
    ),
    query_type: QueryType = Query(default=QueryType.SMART, description="Query type")
):
    try:
        handler = QueryHandler(org_id=org_id, project_id=project_id)
        result = await handler.query(query=query, query_type=query_type, document_id=document_id, top_k=top_k)
        if not result:
            logger.error({"message": "Failed to query", "result": result})
            return error_response("Failed to query", HTTP_404_NOT_FOUND)
        return success_response(data=result)
    except Exception as e:
        logger.error({"message": "Failed to query", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
