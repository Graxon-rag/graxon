from .interfaces.chunk_interface import N4jChunkInterface
from app.constants.neo4j import GN4jNodes, GNeo4jEdges
from ..databases.neo4j.client import GNeo4jClient
from typing import cast, LiteralString, Literal
from ..schemas import graph_schema as gs
from app.utils.logger import logger
from typing import Optional, List
from .interfaces import common
import uuid
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


class GN4jChunkClient:
    def __init__(self):
        self.graph = GNeo4jClient.get_driver()

    async def get_chunks(self, chunk_id: Optional[str] = None, limit: int = 10, offset: int = 0) -> gs.GN4jChunkGetSchema:
        try:
            skip = 0
            if offset > 0:
                skip = (offset - 1) * limit

            where_clause = f"WHERE c.{N4jChunkInterface.id} = $chunk_id" if chunk_id else ""
            params = {"chunk_id": chunk_id} if chunk_id else {}

            # Count query
            query = cast(LiteralString, f"""
                MATCH (c:{GN4jNodes.CHUNK})
                {where_clause}
                RETURN count(c) AS total
            """)

            # Data query
            data_query = cast(LiteralString, f"""
                MATCH (c:{GN4jNodes.CHUNK})
                {where_clause}
                RETURN c
                ORDER BY c.created_at DESC
                SKIP {skip}
                LIMIT {limit}
            """)

            count_result = await self.graph.execute_query(query, parameters_=params)
            total = count_result[0][0]["total"] if count_result[0] else 0
            total_pages = math.ceil(total / limit) if total > 0 else 1
            current_page = offset if offset > 0 else 1

            data_result = await self.graph.execute_query(data_query, parameters_=params)

            chunks = [gs.N4jChunkSchema(**dict(record["c"])) for record in data_result[0]]
            return gs.GN4jChunkGetSchema(
                data=chunks,
                pagination=gs.Pagination(
                    current_page=current_page,
                    total_pages=total_pages,
                    current_limit=limit,
                    total_items=total,
                    has_next=current_page < total_pages,
                    has_previous=current_page > 1,
                ),
            )
        except Exception as e:
            logger.error({"message": "Failed to get chunks", "error": str(e)})
            raise e


class GN4jMappingClient:
    def __init__(self, org_id: str, project_id: uuid.UUID,):
        self.org_id = org_id
        self.project_id = project_id
        self.graph = GNeo4jClient.get_driver()

    async def get_mapping_for_org_project(
        self,
        edge_type: Literal[
            GNeo4jEdges.HAS_TAG,      # type: ignore
            GNeo4jEdges.HAS_ENTITY,   # type: ignore
            GNeo4jEdges.HAS_CONCEPT,  # type: ignore
            GNeo4jEdges.HAS_KEYWORD,  # type: ignore
            GNeo4jEdges.HAS_PHRASE,   # type: ignore
            GNeo4jEdges.HAS_ACRONYM,  # type: ignore
        ],
        is_all: bool = False,
        limit: int = 10,
        offset: int = 0,
    ) -> List[gs.N4jCommonEdgeChunksSchema]:
        try:
            skip = 0
            if offset > 0:
                skip = (offset - 1) * limit

            # Map each edge type to its target node label
            edge_to_node: dict = {
                GNeo4jEdges.HAS_TAG: GN4jNodes.TAG,
                GNeo4jEdges.HAS_ENTITY: GN4jNodes.ENTITY,
                GNeo4jEdges.HAS_CONCEPT: GN4jNodes.CONCEPT,
                GNeo4jEdges.HAS_KEYWORD: GN4jNodes.KEYWORD,
                GNeo4jEdges.HAS_PHRASE: GN4jNodes.PHRASE,
                GNeo4jEdges.HAS_ACRONYM: GN4jNodes.ACRONYM,
            }
            node_label = edge_to_node[edge_type]

            exists_query = """
                CALL db.relationshipTypes() YIELD relationshipType
                WHERE relationshipType = $rel_type
                RETURN count(*) AS count
            """
            exists_result = await self.graph.execute_query(
                exists_query,
                parameters_={"rel_type": edge_type},
            )
            exists_rows = [dict(zip(exists_result.keys, r)) for r in exists_result.records]
            if not exists_rows or exists_rows[0].get("count", 0) == 0:
                logger.debug(f"Relationship type {edge_type!r} does not exist in graph, skipping.")
                return []

            query = f"""
                MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
                -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
                -[:{GNeo4jEdges.HAS_DOCUMENT}]->(:{GN4jNodes.DOCUMENT})
                -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})
                -[edge:{edge_type}]->(node:{node_label})
                WHERE edge IS NOT NULL
                RETURN
                    node.id        AS id,
                    node.type      AS type,
                    node.value     AS value,
                    SUM(edge.frequency) AS frequency,
                    COLLECT({{
                        chunk_id  : chunk.id,
                        type      : type(edge),
                        frequency : edge.frequency,
                        weight    : edge.weight
                    }}) AS chunks_ids
                ORDER BY frequency DESC
            """

            if not is_all:
                query += " SKIP $skip LIMIT $limit"

            params = {
                "org_id": self.org_id,
                "project_id": str(self.project_id),
                "skip": skip,
                "limit": limit,
            }

            results = await self.graph.execute_query(cast(LiteralString, query), parameters_=params)
            if not results:
                return []

            keys = results.keys
            rows = [dict(zip(keys, r)) for r in results.records]

            return [
                gs.N4jCommonEdgeChunksSchema(
                    id=row["id"],
                    type=row["type"],
                    value=row["value"],
                    frequency=row["frequency"],
                    chunks_ids=[
                        gs.N4jChunkEdgeCommonSchema(**chunk)
                        for chunk in row["chunks_ids"]
                    ],
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get {edge_type} mapping, error: {e}")
            raise e
