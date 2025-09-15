# ==============================================================================
# Agent: Knowledge Graph Agent
# ==============================================================================
# This agent is the sole gatekeeper for the data persistence layer. It takes
# structured analysis results and is responsible for writing that data into
# Neo4j (for the graph) and PostgreSQL (for relational/document storage).
# ==============================================================================

import logging
from neo4j import GraphDatabase
import psycopg2
from psycopg2.extras import Json
from .analysis_agent import AnalysisResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kg-agent")

class KnowledgeGraphAgent:
    def __init__(self, neo4j_driver, pg_pool):
        self.neo4j_driver = neo4j_driver
        self.pg_pool = pg_pool

    def write_document_to_postgres(self, doc_id: str, source_url: str, raw_text: str, analysis: AnalysisResult):
        """Writes the core document and its analysis to PostgreSQL."""
        conn = None
        try:
            conn = self.pg_pool.getconn()
            with conn.cursor() as cur:
                logger.info(f"Writing document {doc_id} to PostgreSQL.")
                cur.execute(
                    """
                    INSERT INTO documents (id, source_url, raw_text, summary, topics, entities, processed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id) DO UPDATE SET
                        source_url = EXCLUDED.source_url,
                        raw_text = EXCLUDED.raw_text,
                        summary = EXCLUDED.summary,
                        topics = EXCLUDED.topics,
                        entities = EXCLUDED.entities,
                        processed_at = NOW();
                    """,
                    (
                        doc_id,
                        source_url,
                        raw_text,
                        analysis.summary,
                        analysis.topics,
                        Json([e.model_dump() for e in analysis.entities]),
                    )
                )
            conn.commit()
            logger.info(f"Successfully wrote document {doc_id} to PostgreSQL.")
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error writing to PostgreSQL: {e}")
            raise
        finally:
            if conn:
                self.pg_pool.putconn(conn)

    def write_analysis_to_neo4j(self, doc_id: str, analysis: AnalysisResult):
        """Writes the analyzed entities and relationships to the Neo4j graph."""
        with self.neo4j_driver.session() as session:
            logger.info(f"Writing analysis for doc {doc_id} to Neo4j.")
            try:
                # 1. Create the Document node
                session.run(
                    "MERGE (d:Document {id: $doc_id}) SET d.summary = $summary",
                    doc_id=doc_id, summary=analysis.summary
                )

                # 2. Create Topic nodes and connect them to the Document
                for topic in analysis.topics:
                    session.run(
                        """
                        MERGE (t:Topic {name: $topic_name})
                        WITH t
                        MATCH (d:Document {id: $doc_id})
                        MERGE (d)-[:HAS_TOPIC]->(t)
                        """,
                        topic_name=topic.lower(), doc_id=doc_id
                    )

                # 3. Create Entity nodes and connect them to the Document
                for entity in analysis.entities:
                    # Use MERGE to avoid creating duplicate entities
                    # Create a generic "Entity" node and also a specific type label
                    session.run(
                        f"""
                        MERGE (e:Entity {{name: $name}})
                        ON CREATE SET e.type = $type
                        SET e += {{last_seen: datetime()}}
                        ON MATCH SET e.type = $type
                        WITH e
                        MATCH (d:Document {{id: $doc_id}})
                        MERGE (d)-[r:MENTIONS]->(e)
                        ON CREATE SET r.contexts = [$context]
                        ON MATCH SET r.contexts = r.contexts + $context
                        """,
                        name=entity.name, type=entity.type, context=entity.context, doc_id=doc_id
                    )
                logger.info(f"Successfully wrote analysis for doc {doc_id} to Neo4j.")
            except Exception as e:
                logger.error(f"Error writing to Neo4j: {e}")
                raise

    def run(self, doc_id: str, source_url: str, raw_text: str, analysis: AnalysisResult):
        """The main execution method for the agent."""
        try:
            self.write_document_to_postgres(doc_id, source_url, raw_text, analysis)
            self.write_analysis_to_neo4j(doc_id, analysis)
            return {"status": "success", "doc_id": doc_id}
        except Exception as e:
            return {"status": "error", "doc_id": doc_id, "error": str(e)}
