from starlette.status import (HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND)
from app.utils.response_util import success_response, error_response
from fastapi import HTTPException, APIRouter, Query
from ..neo4j.common import GN4jTagClient
from app.utils.logger import logger
from typing import Optional
import uuid

router = APIRouter(
    tags=["Graph"],
    responses={404: {"description": "Not found"}},
)


@router.get("/tags")
async def get_tags(tag: Optional[str] = Query(default=None, description="Tag name"), limit: int = Query(default=10, ge=1, le=100, description="Number of results"), offset: int = Query(default=0, ge=0, description="Offset")):
    try:
        client = GN4jTagClient()
        return await client.get_tags(tag, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get tags, error : {e}")
        raise e
