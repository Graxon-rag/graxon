from ..schemas.chunk_schema import Chunk, N4jChunkEdge, ChunkPrevNextVecSimilarity, ChunkPrevNext, VectorSimilarity, ChunkPrevNextSchema
from .interfaces.chunk_interface import N4jChunkInterface
from ..schemas.neo4j_schema import LexicalSemanticResult
from app.constants.neo4j import GN4jNodes, GNeo4jEdges
from ..databases.neo4j.client import GNeo4jClient
from typing import cast, LiteralString, Tuple
from app.utils.logger import logger
from .interfaces import common
from itertools import groupby
import hashlib
import uuid


class GN4jChunk:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.graph = GNeo4jClient.get_driver()
        self.org_id = org_id
        self.project_id = project_id

    async def create_multiple(self, document_id: uuid.UUID, document_readable_id: str, chunks: list[Chunk]):
        try:
            # Convert Pydantic models to a list of dictionaries for Neo4j parameters
            chunk_data = [chunk.model_dump() for chunk in chunks]

            query = cast(LiteralString, f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})-[:{GNeo4jEdges.HAS_DOCUMENT}]->(dc:{GN4jNodes.DOCUMENT} {{id: $document_id}})
                WITH dc
                UNWIND $chunks_list AS chunk_item

                MERGE (ch:{GN4jNodes.CHUNK} {{id: chunk_item.chunk_id}})
                SET
                    ch.{N4jChunkInterface.org_id} = $org_id,
                    ch.{N4jChunkInterface.project_id} = $project_id,
                    ch.{N4jChunkInterface.document_id} = $document_id,
                    ch.{N4jChunkInterface.document_readable_id} = $document_readable_id,
                    ch.{N4jChunkInterface.created_at} = datetime(),
                    ch.{N4jChunkInterface.updated_at} = datetime(),
                    ch.{N4jChunkInterface.type} = $type,
                    ch.{N4jChunkInterface.text} = chunk_item.text,
                    ch.{N4jChunkInterface.page_number} = chunk_item.page_number,
                    ch.{N4jChunkInterface.title} = chunk_item.title,
                    ch.{N4jChunkInterface.source} = chunk_item.source,
                    ch.{N4jChunkInterface.chunk_number} = chunk_item.chunk_number

                MERGE (dc)-[:{GNeo4jEdges.HAS_CHUNK}]->(ch)
                RETURN count(ch) as created_count
            """)

            params = {
                "org_id": self.org_id,
                "project_id": str(self.project_id),
                "document_id": str(document_id),
                "document_readable_id": document_readable_id,
                "chunks_list": chunk_data,
                "type": GN4jNodes.CHUNK,
            }

            result, _, _ = await self.graph.execute_query(
                query,
                params,
            )
            logger.info(f"Successfully bulk inserted {result[0]['created_count']} chunks.")
            return result[0]['created_count']

        except Exception as e:
            logger.error({"message": "Failed to create chunks", "error": str(e)})
            raise e

    async def create_acronym_nodes_and_edges(self, document_id: uuid.UUID, acronyms: dict[str, dict]):
        rows = []
        for short, info in acronyms.items():
            node_id = hashlib.md5(short.upper().encode()).hexdigest()
            # defined_in chunk gets weight 1.0, used_in chunks get 0.9
            all_chunks = [(info["defined_in"], 1.0)] + [(cid, 0.9) for cid in info["used_in"]]
            for chunk_id, weight in all_chunks:
                rows.append({
                    "node_id": node_id,
                    "acronym": short.upper(),
                    "expansion": info.get("full", ""),
                    "chunk_id": chunk_id,
                    "weight": weight,
                })

        if not rows:
            return

        query = cast(LiteralString, f"""
            UNWIND $rows AS row
            MERGE (n:{GN4jNodes.ACRONYM} {{id: row.node_id}})
            ON CREATE SET n.{common.N4jAcronymInterface.value} = row.acronym, n.{common.N4jAcronymInterface.expansion} = row.expansion, n.frequency = 1, n.{common.N4jAcronymInterface.type} = $type
            ON MATCH  SET n.{common.N4jAcronymInterface.frequency} = n.frequency + 1
            WITH n, row
            MATCH (c:{GN4jNodes.CHUNK} {{id: row.chunk_id}})
            MERGE (c)-[r:{GNeo4jEdges.HAS_ACRONYM}]->(n)
            ON CREATE SET r.weight = row.weight, r.frequency = 1
            ON MATCH  SET r.frequency = r.frequency + 1
            RETURN count(*) AS merged_count
        """)

        result, _, _ = await self.graph.execute_query(query, {"rows": rows, "type": GN4jNodes.ACRONYM})
        logger.info(f"Merged {result[0]['merged_count']} acronym nodes for document {document_id}.")

    async def create_edges_by_lexical_engine_data(self, document_id: uuid.UUID, document_readable_id: str, lexical_data: LexicalSemanticResult):
        try:
            maps = [
                (lexical_data.entity_map, GN4jNodes.ENTITY, GNeo4jEdges.HAS_ENTITY, common.N4jEntityInterface.value),
                (lexical_data.concept_map, GN4jNodes.CONCEPT, GNeo4jEdges.HAS_CONCEPT, common.N4jConceptInterface.value),
                (lexical_data.keyword_map, GN4jNodes.KEYWORD, GNeo4jEdges.HAS_KEYWORD, common.N4jKeywordInterface.value),
                (lexical_data.phrase_map, GN4jNodes.PHRASE, GNeo4jEdges.HAS_PHRASE, common.N4jPhraseInterface.value),
            ]

            for data_map, node_type, edge_type, value in maps:
                if data_map:
                    await self.create_semantic_nodes_and_edges(
                        document_id=document_id,
                        node_type=node_type,
                        edge_type=edge_type,
                        value_field=value,
                        data=data_map,
                    )

            if lexical_data.acronyms:
                await self.create_acronym_nodes_and_edges(document_id, lexical_data.acronyms)

            logger.info(f"Lexical graph write complete for document {document_readable_id}.")

        except Exception as e:
            logger.error({"message": "Failed to create lexical edges", "error": str(e)})
            raise e

    async def create_semantic_nodes_and_edges(
        self,
        document_id: uuid.UUID,
        node_type: str,
        edge_type: str,
        value_field: str,
        data: dict[str, dict[str, float]],  # {value: {chunk_id: weight}}
    ):
        try:
            rows = []
            for value, chunk_weights in data.items():
                node_id = hashlib.md5(value.lower().strip().encode()).hexdigest()
                for chunk_id, weight in chunk_weights.items():
                    rows.append({
                        "node_id": node_id,
                        "value": value.lower().strip(),
                        "chunk_id": chunk_id,
                        "weight": weight,
                        "type": node_type
                    })

            if not rows:
                return 0

            query = cast(LiteralString, f"""
                UNWIND $rows AS row
                MERGE (n:{node_type} {{id: row.node_id}})
                ON CREATE SET n.{value_field} = row.value, n.frequency = 1, n.type = row.type
                ON MATCH  SET n.frequency = n.frequency + 1
                WITH n, row
                MATCH (c:{GN4jNodes.CHUNK} {{id: row.chunk_id}})
                MERGE (c)-[r:{edge_type}]->(n)
                ON CREATE SET r.weight = row.weight, r.frequency = 1
                ON MATCH  SET r.frequency = r.frequency + 1
                RETURN count(*) AS merged_count
            """)

            result, _, _ = await self.graph.execute_query(query, {"rows": rows})
            count = result[0]["merged_count"]
            logger.info(f"Merged {count} [{edge_type}] nodes for document {document_id}.")
            return count

        except Exception as e:
            logger.error({"message": "Failed to create semantic nodes and edges", "error": str(e)})
            raise e

    async def create_edges(self, document_id: uuid.UUID, edges: list[N4jChunkEdge]):
        try:
            sorted_edges = sorted(edges, key=lambda e: e.edge_name)
            grouped = groupby(sorted_edges, key=lambda e: e.edge_name)

            total_merged = 0

            for edge_name, edge_group in grouped:
                edge_list = [
                    {
                        "source": e.from_chunk_id,
                        "target": e.to_chunk_id,
                        "label": e.label,
                        "weight": e.weight,
                    }
                    for e in edge_group
                ]
                # Each group does UNWIND $edges — so all HAS_TAG edges merge in one shot, all NEXT edges in one shot etc.
                query = cast(LiteralString, f"""
                    UNWIND $edges AS edge
                    MATCH (src:{GN4jNodes.CHUNK} {{id: edge.source}})
                    MATCH (tgt:{GN4jNodes.CHUNK} {{id: edge.target}})
                    MERGE (src)-[:{edge_name} {{label: edge.label, weight: edge.weight}}]->(tgt)
                    RETURN count(*) AS merged_count
                """)

                result, _, _ = await self.graph.execute_query(query, {"edges": edge_list})
                count = result[0]["merged_count"]
                total_merged += count
                logger.info(f"Merged {count} [{edge_name}] edges for document {document_id}.")

            logger.info(f"Total edges merged: {total_merged} for document {document_id}.")
            return total_merged

        except Exception as e:
            logger.error({"message": "Failed to create edges", "error": str(e)})
            raise e

    async def delete_by_doc_id(self, document_id: uuid.UUID):
        try:
            query = cast(LiteralString, f"""
                MATCH (og:{GN4jNodes.ORGANIZATION} {{id: $org_id}})-[:{GNeo4jEdges.HAS_PROJECT}]->(pr:{GN4jNodes.PROJECT} {{id: $project_id}})
                MATCH (pr)-[:{GNeo4jEdges.HAS_DOCUMENT}]->(dc:{GN4jNodes.DOCUMENT} {{id: $document_id}})
                MATCH (dc)-[:{GNeo4jEdges.HAS_CHUNK}]->(ch:{GN4jNodes.CHUNK})
                DETACH DELETE ch
            """)

            await self.graph.execute_query(query, {"org_id": self.org_id, "project_id": str(self.project_id), "document_id": str(document_id)})

        except Exception as e:
            logger.error({"message": "Failed to delete chunks", "error": str(e)})
            raise e

    async def get_prev_next_chunks(self, chunk_id_scores: list[Tuple[str, float]], document_id: uuid.UUID | None = None) -> list[ChunkPrevNextSchema]:
        try:

            # Extract ids and preserve scores
            chunk_ids = [chunk_id for chunk_id, _ in chunk_id_scores]
            score_map = {chunk_id: score for chunk_id, score in chunk_id_scores}

            document_filter = "AND d.id = $document_id" if document_id else ""

            query = f"""
                MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
                -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
                -[:{GNeo4jEdges.HAS_DOCUMENT}]->(d:{GN4jNodes.DOCUMENT})
                -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})

                WHERE chunk.id IN $chunk_ids
                {document_filter}

                OPTIONAL MATCH (chunk)-[prev_rel:{GNeo4jEdges.PREV}]->(prev_chunk:{GN4jNodes.CHUNK})
                OPTIONAL MATCH (chunk)-[next_rel:{GNeo4jEdges.NEXT}]->(next_chunk:{GN4jNodes.CHUNK})
                RETURN
                    chunk.id                    AS chunk_id,
                    chunk.text                  AS chunk_text,
                    chunk.chunk_number          AS chunk_number,
                    prev_chunk.id               AS prev_chunk_id,
                    prev_chunk.text             AS prev_chunk_text,
                    prev_chunk.chunk_number     AS prev_chunk_number,
                    prev_rel.weight             AS prev_chunk_weight,
                    next_chunk.id               AS next_chunk_id,
                    next_chunk.text             AS next_chunk_text,
                    next_chunk.chunk_number     AS next_chunk_number,
                    next_rel.weight             AS next_chunk_weight
            """
            params = {
                "org_id": str(self.org_id),
                "project_id": str(self.project_id),
                "document_id": str(document_id) if document_id else None,
                "chunk_ids": chunk_ids,
            }

            results = await self.graph.execute_query(query, params)

            if not results:
                return []

            keys = results.keys
            rows = [dict(zip(keys, r)) for r in results.records]                                                                               
            return [
                ChunkPrevNextSchema(
                    chunk_id=row["chunk_id"],
                    text=row["chunk_text"],
                    chunk_number=row["chunk_number"],
                    weight=1.0,
                    point_score=score_map[row["chunk_id"]],
                    prev_chunk=ChunkPrevNext(
                        chunk_id=row["prev_chunk_id"],
                        text=row["prev_chunk_text"],
                        weight=row["prev_chunk_weight"],
                        chunk_number=row["prev_chunk_number"],
                    ) if row["prev_chunk_id"] is not None else None,
                    next_chunk=ChunkPrevNext(
                        chunk_id=row["next_chunk_id"],
                        text=row["next_chunk_text"],
                        weight=row["next_chunk_weight"],
                        chunk_number=row["next_chunk_number"],
                    ) if row["next_chunk_id"] is not None else None,
                )
                for row in rows
            ]
        except Exception as e:
            logger.error({"message": "Failed to get prev/next chunks", "error": str(e)})
            raise e

    # async def get_prev_next_vector_similar_chunks(
    #     self,
    #     chunk_ids: list[str],
    #     gte__vector_score: float = 0.80,
    #     document_id: uuid.UUID | None = None
    # ) -> List[ChunkPrevNextVecSimilarity]:
    #     try:
    #         query = f"""
    #             MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
    #             -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
    #             -[:{GNeo4jEdges.HAS_DOCUMENT}]->(d:{GN4jNodes.DOCUMENT})
    #             -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})
    #             WHERE chunk.id IN $chunk_ids

    #             // PREV chunk
    #             OPTIONAL MATCH (chunk)-[prev_rel:{GNeo4jEdges.PREV}]->(prev_chunk:{GN4jNodes.CHUNK})

    #             // NEXT chunk
    #             OPTIONAL MATCH (chunk)-[next_rel:{GNeo4jEdges.NEXT}]->(next_chunk:{GN4jNodes.CHUNK})

    #             // VECTOR_SIMILARITY chunks
    #             OPTIONAL MATCH (chunk)-[vs_rel:{GNeo4jEdges.VECTOR_SIMILARITY}]->(vs_chunk:{GN4jNodes.CHUNK})
    #             WHERE vs_rel.weight >= $gte__vector_score

    #             RETURN
    #                 chunk.id                    AS chunk_id,
    #                 prev_chunk.id               AS prev_chunk_id,
    #                 prev_chunk.text             AS prev_chunk_text,
    #                 prev_rel.weight             AS prev_chunk_weight,
    #                 next_chunk.id               AS next_chunk_id,
    #                 next_chunk.text             AS next_chunk_text,
    #                 next_rel.weight             AS next_chunk_weight,
    #                 collect({{
    #                     chunk_id: vs_chunk.id,
    #                     text:     vs_chunk.text,
    #                     score:    vs_rel.weight
    #                 }})                         AS vector_similar_chunks
    #         """

    #         params = {
    #             "org_id": str(self.org_id),
    #             "project_id": str(self.project_id),
    #             "document_id": str(document_id) if document_id else None,
    #             "chunk_ids": chunk_ids,
    #             "gte__vector_score": gte__vector_score,
    #         }

    #         results = await self.graph.execute_query(query, params)

    #         if not results:
    #             return []

    #         keys = results.keys
    #         rows = [dict(zip(keys, r)) for r in results.records]

    #         return [
    #             ChunkPrevNextVecSimilarity(
    #                 chunk_id=row["chunk_id"],
    #                 prev_chunk=ChunkPrevNext(
    #                     chunk_id=row["prev_chunk_id"],
    #                     text=row["prev_chunk_text"],
    #                     weight=row["prev_chunk_weight"],
    #                 ) if row["prev_chunk_id"] is not None else None,
    #                 next_chunk=ChunkPrevNext(
    #                     chunk_id=row["next_chunk_id"],
    #                     text=row["next_chunk_text"],
    #                     weight=row["next_chunk_weight"],
    #                 ) if row["next_chunk_id"] is not None else None,
    #                 vector_similar_chunks=[
    #                     VectorSimilarity(chunk_id=c["chunk_id"], text=c["text"], weight=c["score"]) for c in row["vector_similar_chunks"]
    #                     if c["chunk_id"] is not None
    #                 ],
    #             )
    #             for row in rows
    #         ]
    #     except Exception as e:
    #         logger.error({"message": "Failed to get prev next vector similar chunks", "error": str(e)})
    #         raise e


class GN4jChunkEdgeClient:
    def __init__(self, org_id: str, project_id: uuid.UUID):
        self.graph = GNeo4jClient.get_driver()
        self.org_id = org_id
        self.project_id = project_id

    async def get_chunk_ids_by_tag(self, tag_id: str) -> list[str]:
        try:
            query: LiteralString = f"""
            MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
            -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
            -[:{GNeo4jEdges.HAS_DOCUMENT}]->(:{GN4jNodes.DOCUMENT})
            -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})
            -[:{GNeo4jEdges.HAS_TAG}]->(:{GN4jNodes.TAG} {{id: $tag_id}})
            RETURN chunk.id AS chunk_id
            """
            result = await self.graph.execute_query(
                query,
                {"org_id": self.org_id, "project_id": str(self.project_id), "tag_id": tag_id},
            )
            return [record["chunk_id"] for record in result[0]]
        except Exception as e:
            logger.error({"message": "Failed to get chunk ids by tag", "error": str(e)})
            raise e

    async def get_chunk_ids_by_entity(self, entity: str) -> list[str]:
        try:
            query: LiteralString = f"""
            MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
            -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
            -[:{GNeo4jEdges.HAS_DOCUMENT}]->(:{GN4jNodes.DOCUMENT})
            -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})
            -[:{GNeo4jEdges.HAS_ENTITY}]->(:{GN4jNodes.ENTITY} {{id: $entity}})
            RETURN chunk.id AS chunk_id
            """
            result = await self.graph.execute_query(
                query,
                {"org_id": self.org_id, "project_id": str(self.project_id), "entity": entity},
            )
            return [record["chunk_id"] for record in result[0]]
        except Exception as e:
            logger.error({"message": "Failed to get chunk ids by entity", "error": str(e)})
            raise e

    async def get_chunk_ids_by_keyword(self, keyword: str) -> list[str]:
        try:
            query: LiteralString = f"""
            MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
            -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
            -[:{GNeo4jEdges.HAS_DOCUMENT}]->(:{GN4jNodes.DOCUMENT})
            -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})
            -[:{GNeo4jEdges.HAS_KEYWORD}]->(:{GN4jNodes.KEYWORD} {{id: $keyword}})
            RETURN chunk.id AS chunk_id
            """
            result = await self.graph.execute_query(
                query,
                {"org_id": self.org_id, "project_id": str(self.project_id), "keyword": keyword},
            )
            return [record["chunk_id"] for record in result[0]]
        except Exception as e:
            logger.error({"message": "Failed to get chunk ids by keyword", "error": str(e)})
            raise e

    async def get_chunk_ids_by_concept(self, concept: str) -> list[str]:
        try:
            query: LiteralString = f"""
            MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
            -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
            -[:{GNeo4jEdges.HAS_DOCUMENT}]->(:{GN4jNodes.DOCUMENT})
            -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})
            -[:{GNeo4jEdges.HAS_CONCEPT}]->(:{GN4jNodes.CONCEPT} {{id: $concept}})
            RETURN chunk.id AS chunk_id
            """
            result = await self.graph.execute_query(
                query,
                {"org_id": self.org_id, "project_id": str(self.project_id), "concept": concept},
            )
            return [record["chunk_id"] for record in result[0]]
        except Exception as e:
            logger.error({"message": "Failed to get chunk ids by concept", "error": str(e)})
            raise e

    async def get_chunk_ids_by_phrase(self, phrase: str) -> list[str]:
        try:
            query: LiteralString = f"""
            MATCH (:{GN4jNodes.ORGANIZATION} {{id: $org_id}})
            -[:{GNeo4jEdges.HAS_PROJECT}]->(:{GN4jNodes.PROJECT} {{id: $project_id}})
            -[:{GNeo4jEdges.HAS_DOCUMENT}]->(:{GN4jNodes.DOCUMENT})
            -[:{GNeo4jEdges.HAS_CHUNK}]->(chunk:{GN4jNodes.CHUNK})
            -[:{GNeo4jEdges.HAS_PHRASE}]->(:{GN4jNodes.PHRASE} {{id: $phrase}})
            RETURN chunk.id AS chunk_id
            """
            result = await self.graph.execute_query(
                query,
                {"org_id": self.org_id, "project_id": str(self.project_id), "phrase": phrase},
            )
            return [record["chunk_id"] for record in result[0]]
        except Exception as e:
            logger.error({"message": "Failed to get chunk ids by phrase", "error": str(e)})
            raise e
