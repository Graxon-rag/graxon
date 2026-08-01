from app.constants.model_provider import LLMModelProvider, EmbeddingModelProvider, ModelProvider, AudioModelProvider, OCRModelProvider, VideoModelProvider, RerankerModelProvider
from fastapi import APIRouter

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


@router.get("/audio-model")
async def get_audio_model_provider():
    return [e.value for e in AudioModelProvider]


@router.get("/ocr-model")
async def get_ocr_model_provider():
    return [e.value for e in OCRModelProvider]


@router.get("/video-model")
async def get_video_model_provider():
    return [e.value for e in VideoModelProvider]


@router.get("/reranker-model")
async def get_reranker_model_provider():
    return [e.value for e in RerankerModelProvider]


@router.get("/all")
async def get_all():
    return [e.value for e in ModelProvider]
