from ..databases.neo4j.client import GNeo4jClient
from app.constants.neo4j import GN4jNodes
from ..schemas import graph_schema as gs
from typing import cast, LiteralString
from app.utils.logger import logger
from .interfaces import common
from typing import Optional
import math


class GN4jTagClient:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def get_tags(self, tag: Optional[str] = None, limit: int = 10, offset: int = 0) -> gs.GN4jTagGetSchema:
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
            tags = [gs.N4jTagSchema(**dict(record["t"])) for record in data_result[0]]
            return gs.GN4jTagGetSchema(
            data=tags,
            pagination=gs.Pagination(
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


class GN4jEntityClient:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def get_entities(self, entity: Optional[str] = None, limit: int = 10, offset: int = 0) -> gs.GN4jEntityGetSchema:
        try:
            skip = 0
            if offset > 0:
                skip = (offset - 1) * limit

            where_clause = f"WHERE toLower(e.{common.N4jEntityInterface.value}) CONTAINS toLower($entity)" if entity else ""
            params = {"entity": entity} if entity else {}

            # Count query
            count_query = cast(LiteralString, f"""
                MATCH (e:{GN4jNodes.ENTITY})
                {where_clause}
                RETURN count(e) AS total
            """)

            # Data query
            data_query = cast(LiteralString, f"""
                MATCH (e:{GN4jNodes.ENTITY})
                {where_clause}
                RETURN e
                ORDER BY e.created_at DESC
                SKIP {skip}
                LIMIT {limit}
            """)

            count_result = await self.graph.execute_query(count_query, parameters_=params)
            total = count_result[0][0]["total"] if count_result[0] else 0
            total_pages = math.ceil(total / limit) if total > 0 else 1
            current_page = offset if offset > 0 else 1

            data_result = await self.graph.execute_query(data_query, parameters_=params)
            entities = [gs.N4jEntitySchema(**dict(record["e"])) for record in data_result[0]]
            return gs.GN4jEntityGetSchema(
                data=entities,
                pagination=gs.Pagination(
                    current_page=current_page,
                    total_pages=total_pages,
                    current_limit=limit,
                    total_items=total,
                    has_next=current_page < total_pages,
                    has_previous=current_page > 1,
                )
            )
        except Exception as e:
            logger.error(f"Failed to get entities, error : {e}")
            raise e


class GN4jConceptClient:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def get_concepts(self, concept: Optional[str] = None, limit: int = 10, offset: int = 0) -> gs.GN4jConceptGetSchema:
        try:
            skip = 0
            if offset > 0:
                skip = (offset - 1) * limit

            where_clause = f"WHERE toLower(c.{common.N4jConceptInterface.value}) CONTAINS toLower($concept)" if concept else ""
            params = {"concept": concept} if concept else {}

            # Count query
            count_query = cast(LiteralString, f"""
                MATCH (c:{GN4jNodes.CONCEPT})
                {where_clause}
                RETURN count(c) AS total
            """)

            # Data query
            data_query = cast(LiteralString, f"""
                MATCH (c:{GN4jNodes.CONCEPT})
                {where_clause}
                RETURN c
                ORDER BY c.created_at DESC
                SKIP {skip}
                LIMIT {limit}
            """)

            count_result = await self.graph.execute_query(count_query, parameters_=params)
            total = count_result[0][0]["total"] if count_result[0] else 0
            total_pages = math.ceil(total / limit) if total > 0 else 1
            current_page = offset if offset > 0 else 1

            data_result = await self.graph.execute_query(data_query, parameters_=params)
            concepts = [gs.N4jConceptSchema(**dict(record["c"])) for record in data_result[0]]
            return gs.GN4jConceptGetSchema(
                data=concepts,
                pagination=gs.Pagination(
                    current_page=current_page,
                    total_pages=total_pages,
                    current_limit=limit,
                    total_items=total,
                    has_next=current_page < total_pages,
                    has_previous=current_page > 1,
                )
            )
        except Exception as e:
            logger.error(f"Failed to get concepts, error : {e}")
            raise e


class GN4jKeywordClient:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def get_keywords(self, keyword: Optional[str] = None, limit: int = 10, offset: int = 0) -> gs.GN4jKeywordGetSchema:
        try:
            skip = 0
            if offset > 0:
                skip = (offset - 1) * limit

            where_clause = f"WHERE toLower(k.{common.N4jKeywordInterface.value}) CONTAINS toLower($keyword)" if keyword else ""
            params = {"keyword": keyword} if keyword else {}

            # Count query
            count_query = cast(LiteralString, f"""
                MATCH (k:{GN4jNodes.KEYWORD})
                {where_clause}
                RETURN count(k) AS total
            """)

            # Data query
            data_query = cast(LiteralString, f"""
                MATCH (k:{GN4jNodes.KEYWORD})
                {where_clause}
                RETURN k
                ORDER BY k.created_at DESC
                SKIP {skip}
                LIMIT {limit}
            """)

            count_result = await self.graph.execute_query(count_query, parameters_=params)
            total = count_result[0][0]["total"] if count_result[0] else 0
            total_pages = math.ceil(total / limit) if total > 0 else 1
            current_page = offset if offset > 0 else 1

            data_result = await self.graph.execute_query(data_query, parameters_=params)
            keywords = [gs.N4jKeywordSchema(**dict(record["k"])) for record in data_result[0]]
            return gs.GN4jKeywordGetSchema(
                data=keywords,
                pagination=gs.Pagination(
                    current_page=current_page,
                    total_pages=total_pages,
                    current_limit=limit,
                    total_items=total,
                    has_next=current_page < total_pages,
                    has_previous=current_page > 1,
                )
            )
        except Exception as e:
            logger.error(f"Failed to get keywords, error : {e}")
            raise e


class GN4jPhraseClient:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def get_phrases(self, phrase: Optional[str] = None, limit: int = 10, offset: int = 0) -> gs.GN4jPhraseGetSchema:
        try:
            skip = 0
            if offset > 0:
                skip = (offset - 1) * limit

            where_clause = f"WHERE toLower(p.{common.N4jPhraseInterface.value}) CONTAINS toLower($phrase)" if phrase else ""
            params = {"phrase": phrase} if phrase else {}

            # Count query
            count_query = cast(LiteralString, f"""
                MATCH (p:{GN4jNodes.PHRASE})
                {where_clause}
                RETURN count(p) AS total
            """)

            # Data query
            data_query = cast(LiteralString, f"""
                MATCH (p:{GN4jNodes.PHRASE})
                {where_clause}
                RETURN p
                ORDER BY p.created_at DESC
                SKIP {skip}
                LIMIT {limit}
            """)

            count_result = await self.graph.execute_query(count_query, parameters_=params)
            total = count_result[0][0]["total"] if count_result[0] else 0
            total_pages = math.ceil(total / limit) if total > 0 else 1
            current_page = offset if offset > 0 else 1

            data_result = await self.graph.execute_query(data_query, parameters_=params)
            phrases = [gs.N4jPhraseSchema(**dict(record["p"])) for record in data_result[0]]
            return gs.GN4jPhraseGetSchema(
                data=phrases,
                pagination=gs.Pagination(
                    current_page=current_page,
                    total_pages=total_pages,
                    current_limit=limit,
                    total_items=total,
                    has_next=current_page < total_pages,
                    has_previous=current_page > 1,
                )
            )
        except Exception as e:
            logger.error(f"Failed to get phrases, error : {e}")
            raise e
