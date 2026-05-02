from fastapi import APIRouter
from app.constants.model_provider import LLMModelProvider, EmbeddingModelProvider

router = APIRouter(
    tags=["Model Provider"],
    # dependencies=[Depends(verify_token)],
    responses={404: {"description": "Not found"}},
)


@router.get("/llm_model")
async def get_llm_model_provider():
    return [e.value for e in LLMModelProvider]


@router.get("/embedding_model")
async def get_embedding_model_provider():
    return [e.value for e in EmbeddingModelProvider]
