# ==============================================================================
# Agentic Knowledge Graph Service - V2
# ==============================================================================
# This updated service now orchestrates the full ingestion pipeline, from
# receiving raw text to analysis and final storage in the knowledge graph.
# ==============================================================================

import os
import logging
import hashlib
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from neo4j import GraphDatabase
from psycopg2.pool import SimpleConnectionPool

# --- Import Agents ---
from agents.analysis_agent import DocumentAnalysisAgent, AnalysisResult
from agents.knowledge_graph_agent import KnowledgeGraphAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentic-kg")

# --- Environment & Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localai:8080")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4-turbo")

# --- Database Connections ---
pg_pool = SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)
neo4j_driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- Agent Instantiation ---
analysis_agent = DocumentAnalysisAgent(llm_service_url=LLM_SERVICE_URL, model_name=LLM_MODEL_NAME)
kg_agent = KnowledgeGraphAgent(neo4j_driver=neo4j_driver, pg_pool=pg_pool)

app = FastAPI(title="Agentic Knowledge Graph API")

# --- API Models ---
class ProcessRequest(BaseModel):
    source_url: str
    raw_text: str

class QueryResponse(BaseModel):
    nodes: list
    edges: list

# --- Core Processing Pipeline ---
async def process_and_store_document(source_url: str, raw_text: str):
    """
    The main background task that runs the full agent pipeline.
    1. Analyze the text to get structured data.
    2. Write the results to the knowledge graph and databases.
    """
    try:
        logger.info(f"Starting analysis for URL: {source_url}")
        analysis_result = await analysis_agent.analyze(raw_text)

        # Generate a stable ID for the document based on its URL
        doc_id = hashlib.sha256(source_url.encode()).hexdigest()

        logger.info(f"Handing off doc {doc_id} to the Knowledge Graph Agent.")
        kg_agent.run(doc_id=doc_id, source_url=source_url, raw_text=raw_text, analysis=analysis_result)
    except Exception as e:
        logger.error(f"Full processing pipeline failed for {source_url}: {e}")

# --- API Endpoints ---
@app.post("/api/v1/kg/process-document")
async def process_document_endpoint(request: ProcessRequest, background_tasks: BackgroundTasks):
    """
    Receives raw text from the crawler and triggers the full
    analysis and ingestion pipeline as a background task.
    """
    background_tasks.add_task(process_and_store_document, request.source_url, request.raw_text)
    return {"status": "processing_started", "source_url": request.source_url}

@app.get("/api/v1/kg/query-entity")
async def query_entity(name: str):
    """
    Queries the knowledge graph for a specific entity and its connections.
    """
    logger.info(f"Querying Neo4j for entity: {name}")
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (e:Entity {name: $name})-[r]-(neighbor)
            RETURN e, r, neighbor
            LIMIT 25
        """, name=name)
        
        nodes = []
        edges = []
        node_ids = set()

        for record in result:
            source_node = record["e"]
            rel = record["r"]
            target_node = record["neighbor"]

            if source_node.id not in node_ids:
                nodes.append({"id": source_node.id, "label": list(source_node.labels)[0], "name": source_node["name"]})
                node_ids.add(source_node.id)
            
            if target_node.id not in node_ids:
                nodes.append({"id": target_node.id, "label": list(target_node.labels)[0], "name": target_node["name"]})
                node_ids.add(target_node.id)

            edges.append({"from": rel.start_node.id, "to": rel.end_node.id, "type": type(rel).__name__})

    return QueryResponse(nodes=nodes, edges=edges)


@app.on_event("shutdown")
def shutdown_event():
    neo4j_driver.close()
    pg_pool.closeall()
    logger.info("Database connections closed.")

@app.get("/health")
async def health():
    return {"status": "ok"}
