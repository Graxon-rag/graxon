from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from app.utils.response_util import success_response, error_response
from ..schemas.query_schema import QueryType, QueryDepth, GQuery
from fastapi import HTTPException, APIRouter, Query, Body
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
    query_type: QueryType = Query(default=QueryType.SMART, description="Query type"),
    query_depth: QueryDepth = Query(default=QueryDepth.STANDARD, description="Query depth")
):
    try:
        handler = QueryHandler(org_id=org_id, project_id=project_id)
        result = await handler.query(GQuery(query=query, top_k=top_k, document_id=document_id, query_type=query_type, query_depth=query_depth))
        if not result:
            logger.error({"message": "Failed to query", "result": result})
            return error_response("Failed to query", HTTP_404_NOT_FOUND)

        if isinstance(result, str):
            return success_response(data={"answer": result})

        return success_response(data=result)
    except Exception as e:
        logger.error({"message": "Failed to query", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
