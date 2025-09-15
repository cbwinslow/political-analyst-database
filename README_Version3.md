# Civic Legislative Hub (v0.4.0)

## Overview
A modular yet single-entry orchestrator (`civic_legis_hub.py`) for ingesting legislative texts and votes, building semantic retrieval (pgvector), generating plain-language summaries, constructing knowledge graphs (FalkorDB / Neo4j optional), integrating doc2graph for text-to-graph triples, and offering an agentic API.

## Key Integrations
| Layer | Integration |
|-------|-------------|
| Storage | PostgreSQL + pgvector (primary) |
| Graph (optional) | FalkorDB (Redis protocol), Neo4j + Bloom export |
| RAG | Sentence-Transformers embeddings |
| Summarization | LocalAI or OpenAI-compatible |
| Ingestion | govinfo (federal), OpenStates (state), ProPublica votes, local file system |
| Knowledge Graph | doc2graph triples -> FalkorDB/Neo4j |
| Agent Memory | Stubs for mcp-memory-libsql, mcp-neo4j-agent-memory, memonto, aius |
| Conversation Graph | Graphiti (optional logging) |
| Pipeline Trigger | RAGFlow endpoint stub |

## File List
- `civic_legis_hub.py` (Main orchestrator & API)
- `tests/test_schema.py`
- `tests/test_embedding.py`
- `tests/test_agent.py`
- `sample_queries.sql`
- `docker-compose.yml`
- `Dockerfile`
- `.env.example`
- `bloom_perspective.json` (export generated if Neo4j enabled)
- (Optional) `scripts/*.sh` you may add for automation

## Quick Start (Local)
```bash
python -m venv .venv
source .venv/bin/activate
export POSTGRES_PASSWORD=postgres
export POSTGRES_USER=postgres
export POSTGRES_DB=civic_kg
docker run -d --name civic_pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector
pip install -r <(echo "requests\ntqdm\npsycopg2-binary\npydantic\nfastapi\nuvicorn\npython-dotenv\nsentence-transformers\nnumpy\nscikit-learn\nbeautifulsoup4\nlxml\nPyPDF2")
python civic_legis_hub.py --init-db
python civic_legis_hub.py --sync-govinfo --govinfo-collections BILLSTATUS,PLAW --govinfo-days 5
python civic_legis_hub.py --sync-openstates --openstates-states "California,New York" --openstates-pages 1
python civic_legis_hub.py --propublica-sync --congress 118 --propublica-chambers house,senate
python civic_legis_hub.py --embed
python civic_legis_hub.py --build-profiles
python civic_legis_hub.py --serve --port 8095
```

## Docker
```bash
cp .env.example .env
# Fill in keys: GOVINFO_API_KEY, PROPUBLICA_API_KEY, OPENSTATES_API_KEY, etc.
docker compose up -d --build
```
API: `http://localhost:8095/health`

## Example API Calls
```bash
curl -X POST http://localhost:8095/query -H "Content-Type: application/json" \
  -d '{"query":"Explain HR-1234 privacy provisions","k":5,"plain":false}'

curl -X POST http://localhost:8095/bill -H "Content-Type: application/json" \
  -d '{"bill_id":"HR-1234","plain":true}'
```

## Politician Profiles
After running `--build-profiles`, query a profile:
```bash
curl -X POST http://localhost:8095/politician -H "Content-Type: application/json" \
  -d '{"politician_id":"SOME_MEMBER_ID"}'
```

## RAGFlow Integration
Use `--ragflow-trigger-url https://your-ragflow/pipeline` to POST a JSON summary after each ingestion.

## FalkorDB
Enable with:
```
export ENABLE_FALKORDB=1
docker run -d --name falkor -p 6379:6379 falkordb/falkordb
python civic_legis_hub.py --populate-falkordb ...
```

## Neo4j + Bloom
Set `ENABLE_NEO4J=1` and Neo4j env vars. Use `--export-bloom` to generate `bloom_perspective.json`.

## Tests
```bash
pip install pytest
pytest -q
```

## Sample Queries
See `sample_queries.sql`.

## Extending
- Add enhanced doc2graph schema mapping
- Build advanced GraphRAG (graph path expansions feeding RAG)
- Integrate Graphiti real memory graph
- Add ingestion adapters for municipal sources (e.g., city council open data portals)

## Disclaimers
Plain-language summaries are not legal advice. Validate with qualified legal professionals. Respect data source rate limits & policies.
