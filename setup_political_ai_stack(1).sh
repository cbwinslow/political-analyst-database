#!/usr/bin/env bash
# Name: Political AI Stack Bootstrapper
# Date: 2025-09-09
# Script Name: setup_political_ai_stack.sh
# Version: 0.9.0
# Log Summary:
#   - 2025-09-09  v0.9.0  Initial scaffold that writes a full docker-compose stack and a Python-based agentic knowledge-graph service.
# Description:
#   This single-script bootstrapper scaffolds a deployable political-document analysis platform.
#   It creates a folder with a docker-compose.yml containing a multi-service stack (Postgres with pgvector init, Neo4j, Milvus (vector DB),
#   Redis, LocalAI, OpenWebUI, Graphite, a small Supabase-like PostgREST service, and a buildable Python "agentic-knowledge-graph" service).
#   The agentic-kg service provides simple endpoints for ingesting docs, translating legislation to plain English, and analyzing politicians
#   using LLMs (via LocalAI) and a knowledge-graph (Neo4j). The script writes all scaffolding files and can launch the stack.
# Change Summary:
#   - Creates project directory: ./political_ai_stack
#   - Writes docker-compose.yml with many configurable services
#   - Writes a minimal FastAPI service (agentic-kg) in ./agentic_kg that integrates Postgres, Neo4j, and LocalAI
#   - Writes .env and init SQL for Postgres (attempts to create pgvector extension)
# Inputs:
#   - None required (optional: edit the generated .env before bringing up the stack)
# Outputs:
#   - Directory ./political_ai_stack with docker-compose.yml, .env, agentic_kg service (Dockerfile + app), and initialization SQL
#   - After execution, containers can be started with 'docker compose up -d' from inside ./political_ai_stack
#
# IMPORTANT NOTES:
#   - This script aims to produce a robust, local-first stack. Some third-party images and extension availability may vary with time.
#   - You should inspect and, if desired, replace placeholders (notably images labeled as "placeholder" or "optional") with maintained images.
#   - For production / remote deploy, adjust secrets and persistent volumes, enable backups, and secure network access.
#
# Usage:
#   Make executable: chmod +x setup_political_ai_stack.sh
#   Run: ./setup_political_ai_stack.sh
#   Then: cd political_ai_stack && docker compose up -d
#
# End header
set -euo pipefail

ROOT_DIR="./political_ai_stack"
AGENT_DIR="$ROOT_DIR/agentic_kg"

echo "Creating project directory at $ROOT_DIR..."
mkdir -p "$AGENT_DIR"

echo "Writing .env..."
cat > "$ROOT_DIR/.env" <<'ENV'
# Postgres settings
POSTGRES_USER=poladmin
POSTGRES_PASSWORD=polpass
POSTGRES_DB=policydocs
POSTGRES_PORT=5432

# Neo4j
NEO4J_AUTH=neo4j/neo4jpass

# LocalAI
LOCALAI_API=http://localai:8080
LOCALAI_MODEL=gpt4o-mini # set to a model available locally, or change

# Milvus
MILVUS_HOST=milvus
MILVUS_PORT=19530

# Service ports
AGENTIC_KG_PORT=8000
ENV

echo "Writing docker-compose.yml..."
cat > "$ROOT_DIR/docker-compose.yml" <<'YAML'
version: "3.8"

services:
  # Postgres with data and init SQL to create pgvector extension (if available)
  postgres:
    image: postgres:15
    env_file: ./.env
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
      - ./init_db:/docker-entrypoint-initdb.d:ro
    ports:
      - "${POSTGRES_PORT}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      retries: 10

  # A simple PostgREST to emulate Supabase-like restful access (replace with supabase stack for full Supabase)
  postgrest:
    image: postgrest/postgrest:latest
    depends_on:
      - postgres
    environment:
      PGRST_DB_URI: "postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}"
      PGRST_DB_SCHEMA: "public"
      PGRST_DB_ANON_ROLE: "postgres"
    ports:
      - "3001:3000"

  # Neo4j for knowledge graph
  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=${NEO4J_AUTH}
      - NEO4J_dbms_default__listen__address=0.0.0.0
    volumes:
      - ./neo4j_data:/data
    ports:
      - "7474:7474"
      - "7687:7687"
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_AUTH#*/}", "RETURN 1"]
      interval: 10s
      retries: 10

  # Redis (used by agents/queues)
  redis:
    image: redis:7
    ports:
      - "6379:6379"

  # Milvus vector database (optional but recommended)
  milvus:
    image: milvusdb/milvus:v2.2.9
    environment:
      - TZ=UTC
    ports:
      - "19530:19530"
      - "19121:19121"
    volumes:
      - ./milvus_data:/var/lib/milvus

  # LocalAI - local model server for embeddings and LLM calls
  localai:
    image: localai/localai:latest
    # NOTE: mount models or change command to point to model storage for local inference
    ports:
      - "8080:8080"
    volumes:
      - ./localai_models:/localai/models
    environment:
      - LOG_LEVEL=info

  # OpenWebUI (web UI for local model interaction) - placeholder image, verify official image name
  openwebui:
    image: openwebui/openwebui:latest
    ports:
      - "3002:3000"
    environment:
      - LOCALAI_URL=http://localai:8080

  # Graphite for metrics (optional)
  graphite:
    image: graphiteapp/graphite-statsd:1.1.9
    ports:
      - "80:80"
    volumes:
      - ./graphite_data:/opt/graphite/storage

  # Agentic Knowledge Graph service - our Python app that wires everything together
  agentic-kg:
    build:
      context: ./agentic_kg
      dockerfile: Dockerfile
    depends_on:
      - postgres
      - neo4j
      - localai
      - milvus
    env_file: ./.env
    environment:
      - LOCALAI_API=${LOCALAI_API}
      - NEO4J_URL=bolt://neo4j:7687
      - NEO4J_AUTH=${NEO4J_AUTH}
      - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - MILVUS_HOST=${MILVUS_HOST}
      - MILVUS_PORT=${MILVUS_PORT}
    ports:
      - "${AGENTIC_KG_PORT}:8000"
    volumes:
      - ./agentic_kg/data:/app/data

  # Placeholder for FalkorDB - user requested; left as optional and disabled
  falkordb:
    image: ghcr.io/falkordb/falkordb:latest
    # If this image doesn't exist on your host/registry, comment out this service or replace it with the correct image
    restart: "no"
    deploy:
      replicas: 0

networks:
  default:
    driver: bridge
YAML

echo "Writing Postgres init scripts (init_db/create_extensions.sql)..."
mkdir -p "$ROOT_DIR/init_db"
cat > "$ROOT_DIR/init_db/create_extensions.sql" <<'SQL'
-- Attempt to create pgvector extension; some Postgres images may not include the extension.
-- If this fails, install pgvector in your Postgres image or use an image that bundles it.
CREATE EXTENSION IF NOT EXISTS vector;
-- Create a documents table that stores content and vector embedding
CREATE TABLE IF NOT EXISTS documents (
  id SERIAL PRIMARY KEY,
  title TEXT,
  content TEXT,
  metadata JSONB,
  embedding vector(1536) -- adjust dimension to your model's embedding size
);
SQL

echo "Scaffolding agentic_kg service (FastAPI app + Dockerfile + requirements)..."

# Write Dockerfile
cat > "$AGENT_DIR/Dockerfile" <<'DOCK'
FROM python:3.11-slim
# Header is in bootstrapper script; keep small runtime image here
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential gcc libpq-dev git curl \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y build-essential gcc \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
DOCK

# requirements
cat > "$AGENT_DIR/requirements.txt" <<'REQ'
fastapi
uvicorn[standard]
httpx
psycopg2-binary
neo4j
python-dotenv
pydantic
sqlalchemy
alembic
python-multipart
REQ

# Write simple FastAPI app
cat > "$AGENT_DIR/app.py" <<'PY'
# Small header intentionally omitted here because main header is in the top-level script.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import httpx
import json
import logging
import psycopg2
from neo4j import GraphDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentic-kg")

# Environment
LOCALAI_API = os.getenv("LOCALAI_API", "http://localai:8080")
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://poladmin:polpass@postgres:5432/policydocs")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://neo4j:7687")
NEO4J_AUTH = os.getenv("NEO4J_AUTH", "neo4j/neo4jpass")

# Connect Postgres (simple sync connection for demo)
def get_pg_conn():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Connect Neo4j
neo_user, neo_pwd = NEO4J_AUTH.split("/", 1)
neo_driver = GraphDatabase.driver(NEO4J_URL, auth=(neo_user, neo_pwd))

app = FastAPI(title="Agentic Knowledge Graph - Political AI")

class IngestRequest(BaseModel):
    title: str
    content: str
    metadata: dict = {}

class TranslateRequest(BaseModel):
    text: str
    target: str = "plain_english"

class PoliticianQuery(BaseModel):
    name: str
    limit: int = 10

# Helpers: call localai for embeddings and LLM summarization
async def get_embedding(text: str):
    # LocalAI embedding endpoint depends on your localai configuration.
    # This is a generic wrapper - adjust to your LocalAI API.
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            r = await client.post(f"{LOCALAI_API}/v1/embeddings", json={"input": text, "model": os.getenv('LOCALAI_MODEL', 'embed-model')})
            r.raise_for_status()
            j = r.json()
            # Expect structure like: { "data": [ { "embedding": [...] } ] }
            emb = j.get("data", [{}])[0].get("embedding")
            return emb
        except Exception as e:
            logger.exception("Embedding failed")
            return None

async def summarize_text(text: str):
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # This is a generic LLM call; adjust payload depending on your local LLM server API.
            payload = {
                "model": os.getenv("LOCALAI_MODEL", "gpt-4o-mini"),
                "input": [
                    {"role":"system","content":"You are a helpful assistant that translates legalese into plain English for the average person."},
                    {"role":"user","content": f"Translate the following into simple English: {text}"}
                ]
            }
            r = await client.post(f"{LOCALAI_API}/v1/chat/completions", json=payload)
            r.raise_for_status()
            jr = r.json()
            # Try to extract text
            content = ""
            # Typical structure: choices[0].message.content
            choices = jr.get("choices") or jr.get("outputs") or []
            if choices and isinstance(choices, list):
                first = choices[0]
                if isinstance(first, dict):
                    if "message" in first and isinstance(first["message"], dict):
                        content = first["message"].get("content", "")
                    else:
                        content = first.get("text") or first.get("output") or ""
            if not content:
                content = jr.get("text", "") or json.dumps(jr)
            return content
        except Exception as e:
            logger.exception("Summarization failed")
            raise HTTPException(status_code=500, detail="LLM call failed")

@app.post("/ingest")
async def ingest(req: IngestRequest):
    emb = await get_embedding(req.content)
    if emb is None:
        raise HTTPException(status_code=500, detail="Failed to get embedding")
    # Store in Postgres
    conn = get_pg_conn()
    cur = conn.cursor()
    try:
        # Ensure embedding length matches; we store in json if vector extension not available
        # Try to insert into vector column if possible; fallback to storing JSON in metadata.
        try:
            # If pgvector is available, embed length must match vector column
            cur.execute("INSERT INTO documents (title, content, metadata, embedding) VALUES (%s, %s, %s, %s) RETURNING id",
                        (req.title, req.content, json.dumps(req.metadata), emb))
        except Exception:
            cur.execute("INSERT INTO documents (title, content, metadata) VALUES (%s, %s, %s) RETURNING id",
                        (req.title, req.content, json.dumps({"embedding": emb, **req.metadata})))
        docid = cur.fetchone()[0]
        conn.commit()
    finally:
        cur.close()
        conn.close()
    # Create a node in Neo4j
    with neo_driver.session() as session:
        session.run("MERGE (d:Document {id:$id}) SET d.title=$title, d.content=$content", id=int(docid), title=req.title, content=req.content)
    return {"status":"ok", "id": docid}

@app.post("/translate")
async def translate(req: TranslateRequest):
    out = await summarize_text(req.text)
    return {"translation": out}

@app.post("/analyze_politician")
async def analyze_politician(q: PoliticianQuery):
    # Placeholder: real implementation would fetch voting records from a source (CSV, API) and query doc store + KG
    name = q.name
    summary = f"Analysis for {name}: (placeholder) - fetch voting records, identify top topics, show alignment with bills."
    # Query Neo4j for nodes with politician name
    with neo_driver.session() as session:
        res = session.run("MATCH (p:Politician {name:$name})-[r]->(o) RETURN type(r) as rel, o LIMIT $limit", name=name, limit=q.limit)
        edges = [{"rel": rec["rel"], "object": dict(rec["o"])} for rec in res]
    return {"summary": summary, "graph_matches": edges}

@app.get("/health")
async def health():
    return {"status":"ok"}
PY

echo "Writing a simple README with usage notes..."
cat > "$ROOT_DIR/README.md" <<'MD'
````markdown
name: README