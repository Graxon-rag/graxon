from ..schemas.graph_schema import GN4jTagGetSchema, Pagination, N4jTagSchema
from ..databases.neo4j.client import GNeo4jClient
from app.constants.neo4j import GN4jNodes
from typing import cast, LiteralString
from app.utils.logger import logger
from .interfaces import common
from typing import Optional
import math


class GN4jTagClient:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def get_tags(self, tag: Optional[str] = None, limit: int = 10, offset: int = 0) -> GN4jTagGetSchema:
        try:
            skip = 0
            if offset > 0:
                skip = (offset - 1) * limit

            where_clause = f"WHERE toLower(t.{common.N4jTagInterface.value}) CONTAINS toLower($tag)" if tag else ""
            params = {"tag": tag} if tag else {}

            # Count query
            count_query = cast(LiteralString, f"""
                MATCH (t:{GN4jNodes.TAG})
                {where_clause}
                RETURN count(t) AS total
            """)

            # Data query
            data_query = cast(LiteralString, f"""
                MATCH (t:{GN4jNodes.TAG})
                {where_clause}
                RETURN t
                ORDER BY t.created_at DESC
                SKIP {skip}
                LIMIT {limit}
            """)

            count_result = await self.graph.execute_query(count_query, parameters_=params)
            total = count_result[0][0]["total"] if count_result[0] else 0
            total_pages = math.ceil(total / limit) if total > 0 else 1
            current_page = offset if offset > 0 else 1

            data_result = await self.graph.execute_query(data_query, parameters_=params)
            tags = [N4jTagSchema(**dict(record["t"])) for record in data_result[0]]
            return GN4jTagGetSchema(
            data=tags,
            pagination=Pagination(
                current_page=current_page,
                total_pages=total_pages,
                current_limit=limit,
                total_items=total,
                has_next=current_page < total_pages,
                has_previous=current_page > 1,
            )
        )
        except Exception as e:
            logger.error(f"Failed to get tags, error : {e}")
            raise e
