from starlette.status import (HTTP_500_INTERNAL_SERVER_ERROR, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND)
from app.utils.response_util import success_response, error_response
from fastapi import HTTPException, APIRouter, Query
from ..neo4j import common
from ..neo4j.chunk import GN4jChunkEdgeClient
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


@router.get("/keywords")
async def get_keywords(keyword: Optional[str] = Query(default=None, description="Keyword name"), limit: int = Query(default=10, ge=1, le=100, description="Number of results"), offset: int = Query(default=0, ge=0, description="Offset")):
    try:
        client = common.GN4jKeywordClient()
        return await client.get_keywords(keyword, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get keywords, error : {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/phrases")
async def get_phrases(phrase: Optional[str] = Query(default=None, description="Phrase name"), limit: int = Query(default=10, ge=1, le=100, description="Number of results"), offset: int = Query(default=0, ge=0, description="Offset")):
    try:
        client = common.GN4jPhraseClient()
        return await client.get_phrases(phrase, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get phrases, error : {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/chunks")
async def get_chunks(chunk_id: Optional[str] = Query(default=None, description="Chunk id"), limit: int = Query(default=10, ge=1, le=100, description="Number of results"), offset: int = Query(default=0, ge=0, description="Offset")):
    try:
        client = common.GN4jChunkClient()
        return await client.get_chunks(chunk_id, limit, offset)
    except Exception as e:
        logger.error(f"Failed to get chunks, error : {e}")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orgs/{org_id}/projects/{project_id}/chunks/tags/{tag_id}")
async def get_chunks_by_tag(org_id: str, project_id: uuid.UUID, tag_id: str):
    try:
        client = GN4jChunkEdgeClient(org_id=org_id, project_id=project_id)
        return await client.get_chunk_ids_by_tag(tag_id)
    except Exception as e:
        logger.error({"message": "Failed to get chunks by tag", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orgs/{org_id}/projects/{project_id}/chunks/entities/{entity_id}")
async def get_chunks_by_entity(org_id: str, project_id: uuid.UUID, entity_id: str):
    try:
        client = GN4jChunkEdgeClient(org_id=org_id, project_id=project_id)
        return await client.get_chunk_ids_by_entity(entity_id)
    except Exception as e:
        logger.error({"message": "Failed to get chunks by entity", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orgs/{org_id}/projects/{project_id}/chunks/keywords/{keyword_id}")
async def get_chunks_by_keyword(org_id: str, project_id: uuid.UUID, keyword_id: str):
    try:
        client = GN4jChunkEdgeClient(org_id=org_id, project_id=project_id)
        return await client.get_chunk_ids_by_keyword(keyword_id)
    except Exception as e:
        logger.error({"message": "Failed to get chunks by keyword", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orgs/{org_id}/projects/{project_id}/chunks/phrases/{phrase_id}")
async def get_chunks_by_phrase(org_id: str, project_id: uuid.UUID, phrase_id: str):
    try:
        client = GN4jChunkEdgeClient(org_id=org_id, project_id=project_id)
        return await client.get_chunk_ids_by_phrase(phrase_id)
    except Exception as e:
        logger.error({"message": "Failed to get chunks by phrase", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/orgs/{org_id}/projects/{project_id}/chunks/concepts/{concept_id}")
async def get_chunks_by_concept(org_id: str, project_id: uuid.UUID, concept_id: str):
    try:
        client = GN4jChunkEdgeClient(org_id=org_id, project_id=project_id)
        return await client.get_chunk_ids_by_concept(concept_id)
    except Exception as e:
        logger.error({"message": "Failed to get chunks by concept", "error": str(e)})
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
