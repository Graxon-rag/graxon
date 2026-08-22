from ..databases.postgresql.client import GPostgresqlClient
from ..databases.postgresql.models import Chunk
from sqlalchemy import select, func, desc, asc
from ..schemas import chunk_schema as cs
from app.utils.logger import logger
import uuid
import math


class ChunkRepo:
    def __init__(self, org_id: str, project_id: uuid.UUID, document_id: uuid.UUID):
        self._db = GPostgresqlClient()
        self.org_id = org_id
        self.project_id = project_id
        self.document_id = document_id

    async def create(self, chunk: cs.ChunkCreateSchema) -> bool:
        try:
            async with self._db.get_session() as session:
                c = Chunk(
                    document_id=self.document_id,
                    chunk_id=chunk.chunk_id,
                    chunk_number=chunk.chunk_number,
                    text=chunk.text,
                    file_chunk_number=chunk.file_chunk_number,
                    chunk_metadata=chunk.metadata
                )
                session.add(c)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create chunk", "error": str(e)})
            raise e

    async def create_multiple(self, chunks: list[cs.ChunkCreateSchema]) -> bool:
        try:
            async with self._db.get_session() as session:
                chunk_models = [Chunk(**chunk.model_dump(), document_id=self.document_id, chunk_metadata=chunk.metadata) for chunk in chunks]
                session.add_all(chunk_models)
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to create chunks", "error": str(e)})
            raise e

    async def update(self, u: cs.ChunkUpdateParams) -> bool:
        try:
            async with self._db.get_session() as session:
                chunk = await session.scalar(select(Chunk).where(Chunk.id == u.id))
                if chunk is None:
                    raise Exception(f"Chunk with id {u.id} not found")
                chunk.text = u.text
                await session.commit()
                return True
        except Exception as e:
            logger.error({"message": "Failed to update chunk", "error": str(e)})
            raise e

    async def get_last_chunk(self) -> cs.ChunkGetSchema | None:
        try:
            async with self._db.get_session() as session:
                chunk = await session.scalar(select(Chunk).where(Chunk.document_id == self.document_id).order_by(desc(Chunk.chunk_number)).limit(1))
                if chunk is None:
                    return None
                return cs.ChunkGetSchema(**chunk.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get last chunk", "error": str(e)})
            raise e

    async def get(self, id: uuid.UUID) -> cs.ChunkGetSchema | None:
        try:
            async with self._db.get_session() as session:
                chunk = await session.scalar(select(Chunk).where(Chunk.id == id))
                if chunk is None:
                    raise Exception(f"Chunk with id {id} not found")
                return cs.ChunkGetSchema(**chunk.to_dict())
        except Exception as e:
            logger.error({"message": "Failed to get chunk", "error": str(e)})
            raise e

    async def get_all_chunk_id_and_number(self) -> list[tuple[str, int]]:
        try:
            async with self._db.get_session() as session:
                stmt = select(Chunk.chunk_id, Chunk.chunk_number).where(
                Chunk.document_id == self.document_id
                )
                stmt = stmt.order_by(asc(Chunk.chunk_number))
                result = await session.execute(stmt)
                return [(row.chunk_id, row.chunk_number) for row in result.all()]
        except Exception as e:
            logger.error({"message": "Failed to get chunk", "error": str(e)})
            raise e

    async def list(self, params: cs.ChunkQueryParams) -> cs.ChunkListSchema:
        try:
            async with self._db.get_session() as session:
                stmt = select(Chunk)
                count_stmt = select(func.count()).select_from(Chunk)

                # Base filter: must belong to the document
                filters = [
                    Chunk.document_id == self.document_id,
                ]

                # Fuzzy search strictly on text
                if params.search:
                    filters.append(Chunk.text.ilike(f"%{params.search.strip()}%"))

                # Exact match on chunk_number
                if params.chunk_number is not None:
                    filters.append(Chunk.chunk_number == params.chunk_number)

                # Exact match on readable chunk_id
                if params.chunk_id:
                    filters.append(Chunk.chunk_id == params.chunk_id)

                # Exact match on primary key UUID
                if params.id:
                    filters.append(Chunk.id == params.id)

                # Apply filters to both statements
                stmt = stmt.where(*filters)
                count_stmt = count_stmt.where(*filters)

                # Count total items
                total_count = await session.scalar(count_stmt) or 0
                total_pages = math.ceil(total_count / params.limit) if total_count > 0 else 1

                # Dynamic Sorting
                sort_column = getattr(Chunk, params.sort_by)

                if params.sort_order == "desc":
                    stmt = stmt.order_by(desc(sort_column))
                else:
                    stmt = stmt.order_by(asc(sort_column))

                # Pagination Offset
                offset = (params.page - 1) * params.limit
                stmt = stmt.offset(offset).limit(params.limit)

                pg_result = await session.execute(stmt)
                result_list = pg_result.scalars().all()

                return cs.ChunkListSchema(
                    data=[cs.ChunkGetSchema(**doc.to_dict()) for doc in result_list],
                    pagination=cs.PaginationSchema(
                        total_pages=total_pages,
                        current_page=params.page,
                        current_limit=params.limit,
                    ),
                )

        except Exception as e:
            logger.error({"message": "Failed to list chunks", "error": str(e)})
            raise e
