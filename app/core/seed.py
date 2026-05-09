from .databases.postgresql.models import Organization, LLMModel, EmbeddingModel, ReRankerModel, SparseTextModel
from .databases.postgresql.client import GPostgresqlClient
from app.utils.logger import logger
from .libs.org_lib import OrgLib
from .neo4j.org import GN4jOrg
from sqlalchemy import select
from sqlalchemy import text
from pathlib import Path
import datetime
import json
import uuid

GRAXON_DATA_PATH = Path(__file__).parent.parent / "graxon_data"


class SeedDefaultData:
    def __init__(self):
        pass

    async def seed(self):
        try:
            logger.info("Seeding default data...")
            await self._ensure_seed_tracker_exists()
            is_first_time = await self._is_first_time_seed()
            if not is_first_time:
                logger.info("Data already seeded. Skipping...")
                return
            await self._pg()
            await self._neo4j()
            await self._mark_as_seeded()
            logger.info("Default data seeded successfully.")
        except Exception as e:
            logger.error({"message": "Failed to seed data", "error": str(e)})
            raise e

    async def _ensure_seed_tracker_exists(self):
        async with GPostgresqlClient.get_session() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS seed_tracker (
                    id SERIAL PRIMARY KEY,
                    seeded BOOLEAN NOT NULL DEFAULT FALSE,
                    seeded_at TIMESTAMP DEFAULT NOW()
                )
            """))
            await session.commit()

    async def _is_first_time_seed(self) -> bool:
        try:
            async with GPostgresqlClient.get_session() as session:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM seed_tracker WHERE seeded = TRUE")
                )
                count = result.scalar()
                return count == 0
        except Exception:
            return True

    async def _mark_as_seeded(self):
        async with GPostgresqlClient.get_session() as session:
            await session.execute(
                text("INSERT INTO seed_tracker (seeded) VALUES (TRUE)")
            )
            await session.commit()

    async def _neo4j(self):
        try:
            org = GN4jOrg()
            await org.create(org_id="dev", name="Development", description="Default Organization")
        except Exception as e:
            logger.error({"message": "Failed to seed neo4j", "error": str(e)})
            raise e

    async def _pg(self):
        try:
            async with GPostgresqlClient.get_session() as session:
                org_id = OrgLib.get_parsed_org_id("dev")
                stmt = select(Organization).where(Organization.id == org_id)
                pg_result = await session.execute(stmt)
                existing = pg_result.scalar_one_or_none()

                if existing is not None:
                    raise Exception(f"Organization with id {org_id} already exists")

                org = Organization(id=org_id, name="Development", description="Default Organization")
                session.add(org)
                await session.flush()

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
                for m in reranker_data:
                    session.add(ReRankerModel(
                        id=uuid.uuid4(),
                        org_id=org_id,
                        name=m["name"],
                        provider=m["provider"],
                        model=m["model"],
                        description=m["description"],
                        size_in_gb=m["size_in_gb"],
                        created_at=now,
                        updated_at=now,
                    ))

                # Sparse Text Models
                sparse_data = json.loads((GRAXON_DATA_PATH / "spare_text_models.json").read_text())
                for m in sparse_data:
                    session.add(SparseTextModel(
                        id=uuid.uuid4(),
                        org_id=org_id,
                        name=m["name"],
                        provider=m["provider"],
                        model=m["model"],
                        description=m["description"],
                        size_in_gb=m["size_in_gb"],
                        created_at=now,
                        updated_at=now,
                    ))

                await session.commit()
                logger.info("PostgreSQL seed data inserted successfully.")

        except Exception as e:
            logger.error({"message": "Failed to seed postgresql", "error": str(e)})
            raise e
