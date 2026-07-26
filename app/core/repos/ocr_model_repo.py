from ..schemas.ocr_model_schema import OCRModelCreateSchema, OCRModelGetSchema
from ..databases.postgresql.client import GPostgresqlClient
from app.constants.model_provider import OCRModelProvider
from ..databases.postgresql.models import OCRModel
from app.utils.logger import logger
from sqlalchemy import select
import uuid


class OCRModelRepo:
    def __init__(self, org_id: str):
        self.db = GPostgresqlClient()
        self.org_id = org_id

    async def create(self, data: OCRModelCreateSchema) -> OCRModelGetSchema:
        try:
            async with self.db.get_session() as session:
                new_ocr_model = OCRModel(
                    org_id=self.org_id,
                    name=data.name,
                    provider=data.provider,
                    model_name=data.model_name,
                    model_id=data.model_id,
                    description=data.description,
                    model_metadata=data.model_metadata or {}
                )
                session.add(new_ocr_model)
                await session.commit()
                get_result = await self.get(new_ocr_model.id)
                if get_result is None:
                    raise Exception(f"OCR model with id {new_ocr_model.id} not found")
                return get_result
        except Exception as e:
            logger.error({"message": "Failed to create OCR model", "error": str(e)})
            raise e

    async def create_multiple(self, ocr_models: list[OCRModelCreateSchema]) -> bool:
        try:
            async with self.db.get_session() as session:
                ocr_model_models = [OCRModel(**ocr_model.model_dump()) for ocr_model in ocr_models]
                session.add_all(ocr_model_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create OCR model", "error": str(e)})
            raise e

    async def get(self, ocr_model_id: uuid.UUID) -> OCRModelGetSchema | None:
        try:
            async with self.db.get_session() as session:
                stmt = select(OCRModel)
                stmt = stmt.where(OCRModel.id == ocr_model_id)
                stmt = stmt.where(OCRModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                ocr_model_model = pg_result.scalars().first()
                if ocr_model_model is None:
                    raise Exception(f"OCR model with id {ocr_model_id} not found")
                return OCRModelGetSchema(**ocr_model_model.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get OCR model", "error": str(e)})
            raise e

    async def get_by_provider(self, provider: OCRModelProvider) -> list[OCRModelGetSchema]:
        try:
            async with self.db.get_session() as session:
                stmt = select(OCRModel)
                stmt = stmt.where(OCRModel.provider == provider)
                stmt = stmt.where(OCRModel.org_id == self.org_id)
                pg_result = await session.execute(stmt)
                result = pg_result.scalars().all()
                return [OCRModelGetSchema(**ocr_model.to_dict()) for ocr_model in result]
        except Exception as e:
            logger.error({"message": "Failed to get OCR model", "error": str(e)})
            raise e

    async def delete(self, ocr_model_id: uuid.UUID) -> bool:
        try:
            async with self.db.get_session() as session:
                stmt = select(OCRModel)
                stmt = stmt.where(OCRModel.id == ocr_model_id)
                stmt = stmt.where(OCRModel.org_id == self.org_id)

                pg_result = await session.execute(stmt)
                if pg_result is None:
                    raise Exception(f"OCR model with id {ocr_model_id} not found")

                ocr_model_model = pg_result.scalars().first()
                await session.delete(ocr_model_model)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to delete OCR model", "error": str(e)})
            raise e
