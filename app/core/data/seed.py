from ..databases.postgresql.models import LLMModel, EmbeddingModel, ReRankerModel, SparseTextModel, AudioModel, VideoModel, OCRModel
from pathlib import Path
import datetime
import json
import uuid

GRAXON_DATA_PATH = Path(__file__).parent.parent.parent / "graxon_data"


async def seed_models(org_id: str, session):
    now = datetime.datetime.now(datetime.timezone.utc)

    # LLM Models
    llm_data = json.loads((GRAXON_DATA_PATH / "llm_models.json").read_text())
    for provider_models in llm_data.values():
        for m in provider_models:
            session.add(LLMModel(
                id=uuid.uuid4(),
                org_id=org_id,
                name=m["name"],
                provider=m["provider"],
                model_name=m["model_name"],
                model_id=m["model_id"],
                description=m["description"],
                created_at=now,
                updated_at=now,
            ))

    # Embedding Models
    embedding_data = json.loads((GRAXON_DATA_PATH / "embedding_model.json").read_text())
    for provider_models in embedding_data.values():
        for m in provider_models:
            session.add(EmbeddingModel(
                id=uuid.uuid4(),
                org_id=org_id,
                name=m["name"],
                provider=m["provider"],
                model_name=m["model_name"],
                model_id=m["model_id"],
                dimension=m["dimension"],
                description=m["description"],
                created_at=now,
                updated_at=now,
            ))

    # Reranker Models
    reranker_data = json.loads((GRAXON_DATA_PATH / "reranker_models.json").read_text())
    for provider_name, provider_data in reranker_data.items():
        print(f"\nProcessing ReRanker {provider_name}: {len(provider_data)} models")

        for m in provider_data:
            # print(f"Adding: {m['name']}")

            try:
                model = ReRankerModel(
                    id=uuid.uuid4(),
                    org_id=org_id,
                    name=m["name"],
                    provider_type=m["provider_type"],
                    provider=m["provider"],
                    model_name=m["model_name"],
                    model_id=m["model_id"],
                    description=m["description"],
                    model_metadata=m["model_metadata"] or {},
                    size_in_gb=m["size_in_gb"],
                    created_at=now,
                    updated_at=now,
                )

                session.add(model)
                # print(f"SUCCESS: {m['name']}")
            except Exception as e:
                print(f"FAILED: {m['name']}: {e}")

    # Sparse Text Models
    sparse_data = json.loads((GRAXON_DATA_PATH / "spare_text_models.json").read_text())
    for provider_name, provider_data in sparse_data.items():
        print(f"\nProcessing Sparse {provider_name}: {len(provider_data)} models")

        for m in provider_data:
            try:
                model = SparseTextModel(
                    id=uuid.uuid4(),
                    org_id=org_id,
                    name=m["name"],
                    provider_type=m["provider_type"],
                    provider=m["provider"],
                    model_name=m["model_name"],
                    model_id=m["model_id"],
                    description=m["description"],
                    model_metadata=m["model_metadata"] or {},
                    size_in_gb=m["size_in_gb"],
                    created_at=now,
                    updated_at=now,
                )

                session.add(model)
            except Exception as e:
                print(f"FAILED: {m['name']}: {e}")

    # Audio/ STT Model
    audio_data = json.loads((GRAXON_DATA_PATH / "audio_model.json").read_text())
    for provider_data in audio_data.values():
        for m in provider_data:
            session.add(AudioModel(
                id=uuid.uuid4(),
                org_id=org_id,
                name=m["name"],
                provider=m["provider"],
                model_name=m["model_name"],
                model_id=m["model_id"],
                description=m["description"],
                model_metadata=m["model_metadata"] or {},
                created_at=now,
                updated_at=now,
            ))

    # OCR Model
    ocr_data = json.loads((GRAXON_DATA_PATH / "ocr_model.json").read_text())
    for provider_data in ocr_data.values():
        for m in provider_data:
            session.add(OCRModel(
                id=uuid.uuid4(),
                org_id=org_id,
                name=m["name"],
                provider=m["provider"],
                model_name=m["model_name"],
                model_id=m["model_id"],
                description=m["description"],
                model_metadata=m["model_metadata"] or {},
                created_at=now,
                updated_at=now,
            ))

    # Video Model
    video_data = json.loads((GRAXON_DATA_PATH / "video_model.json").read_text())
    for provider_data in video_data.values():
        for m in provider_data:
            session.add(VideoModel(
                id=uuid.uuid4(),
                org_id=org_id,
                name=m["name"],
                provider=m["provider"],
                model_name=m["model_name"],
                model_id=m["model_id"],
                description=m["description"],
                model_metadata=m["model_metadata"] or {},
                created_at=now,
                updated_at=now,
            ))

    await session.flush()
