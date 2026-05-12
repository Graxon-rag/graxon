from starlette.status import (HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND)
from app.utils.response_util import success_response, error_response
from fastapi import HTTPException, APIRouter, Query
from ..neo4j import common
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
        client = common.GN4jTagClient()
        return await client.get_tags(tag, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get tags, error : {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/entities")
async def get_entities(entity: Optional[str] = Query(default=None, description="Entity name"), limit: int = Query(default=10, ge=1, le=100, description="Number of results"), offset: int = Query(default=0, ge=0, description="Offset")):
    try:
        client = common.GN4jEntityClient()
        return await client.get_entities(entity, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get entities, error : {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/concepts")
async def get_concepts(concept: Optional[str] = Query(default=None, description="Concept name"), limit: int = Query(default=10, ge=1, le=100, description="Number of results"), offset: int = Query(default=0, ge=0, description="Offset")):
    try:
        client = common.GN4jConceptClient()
        return await client.get_concepts(concept, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get concepts, error : {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
