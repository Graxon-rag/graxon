from .interfaces.chunk_interface import N4jChunkInterface
from app.constants.neo4j import GN4jNodes, GNeo4jEdges
from ..databases.neo4j.client import GNeo4jClient
from ..lexical_engine.index import LexicalResult
from ..schemas.chunk_schema import Chunk
from typing import cast, LiteralString
from app.utils.logger import logger
from itertools import groupby
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
                    ch.{N4jChunkInterface.document_id} = $document_id,
                    ch.{N4jChunkInterface.document_readable_id} = $document_readable_id,
                    ch.{N4jChunkInterface.created_at} = datetime(),
                    ch.{N4jChunkInterface.updated_at} = datetime(),
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
                "chunks_list": chunk_data
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

    async def create_edges_by_lexical_engine_data(self, document_id: uuid.UUID, document_readable_id: str, lexical_data: LexicalResult):
        try:

            # Group edges by edge_type
            sorted_edges = sorted(lexical_data.edges, key=lambda e: e.edge_type)
            grouped = groupby(sorted_edges, key=lambda e: e.edge_type)

            total_merged = 0

            for edge_type, edge_group in grouped:
                edge_list = [
                    {"source": e.source, "target": e.target, "label": e.label, "weight": e.weight}
                    for e in edge_group
                ]
                if edge_type not in [GNeo4jEdges.SHARES_ENTITY, GNeo4jEdges.SHARES_CONCEPT, GNeo4jEdges.SHARES_KEYWORD, GNeo4jEdges.SHARES_PHRASE, GNeo4jEdges.SHARES_ACRONYM]:
                    continue

                query = cast(LiteralString, f"""
                    UNWIND $edges AS edge
                    MATCH (src:{GN4jNodes.CHUNK} {{id: edge.source}})
                    MATCH (tgt:{GN4jNodes.CHUNK} {{id: edge.target}})
                    MERGE (src)-[:{edge_type} {{label: edge.label, weight: edge.weight}}]->(tgt)
                    RETURN count(*) AS merged_count
                """)

                result, _, _ = await self.graph.execute_query(query, {"edges": edge_list})
                count = result[0]["merged_count"]
                total_merged += count
                logger.info(f"Merged {count} [{edge_type}] edges for document {document_readable_id}.")

            logger.info(f"Total edges merged: {total_merged} for document {document_readable_id}.")
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
