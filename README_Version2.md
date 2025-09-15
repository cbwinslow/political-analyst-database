# Civic Legislative Data Stack (PostgreSQL + pgvector + Optional Neo4j)

## Overview
End-to-end pipeline for aggregating legislation (federal, state, local), storing structured data in PostgreSQL with pgvector for retrieval, optionally mirroring bill nodes into Neo4j (for Bloom visualization), and exposing an API that supports semantic queries and plain-language explanations.

## Core Components
- PostgreSQL (primary store)
- pgvector (semantic search)
- Sentence-Transformers embeddings
- Plain-language summarization (LocalAI / OpenAI-compatible)
- govinfo ingestion (federal)
- OpenStates ingestion (state)
- Local file ingestion (municipal / custom)
- Optional Neo4j + Bloom perspective export
- Single script: `civic_legis_stack.py`

## Quick Start (Local)
```bash
python -m venv .venv
source .venv/bin/activate
export POSTGRES_PASSWORD=postgres
export POSTGRES_USER=postgres
export POSTGRES_DB=civic_kg
# Start a local Postgres with pgvector or use docker compose
docker run -d --name civic_pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector
pip install -r <(echo "requests\ntqdm\npsycopg2-binary\npydantic\nfastapi\nuvicorn\npython-dotenv\nsentence-transformers\nnumpy\nscikit-learn\nbeautifulsoup4\nlxml\nPyPDF2")
python civic_legis_stack.py --init-db
python civic_legis_stack.py --sync-govinfo --govinfo-collections BILLSTATUS --govinfo-days 5
python civic_legis_stack.py --sync-openstates --openstates-states "California,New York" --openstates-pages 1
python civic_legis_stack.py --embed
python civic_legis_stack.py --serve
```

Query API:
```bash
curl -X POST http://localhost:8090/query -H "Content-Type: application/json" \
  -d '{"query":"Explain bill HR-1234 privacy impact","k":5,"plain":false}'
```

Fetch Bill (with plain-language):
```bash
curl -X POST http://localhost:8090/bill -H "Content-Type: application/json" \
  -d '{"bill_id":"HR-1234","plain":true}'
```

## Docker Compose
```bash
cp .env.example .env
# Fill secrets (POSTGRES_PASSWORD, GOVINFO_API_KEY, etc.)
docker compose up -d --build
```
API at: http://localhost:8090/health  
Neo4j (if password set): http://localhost:7474  

## Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| POSTGRES_HOST | Host for PostgreSQL | Default: postgres (docker) |
| POSTGRES_PORT | Port | Default: 5432 |
| POSTGRES_DB | Database name | Yes (default civic_kg) |
| POSTGRES_USER | DB user | Yes |
| POSTGRES_PASSWORD | DB password | Yes |
| PGVECTOR_DIM | Embedding dimension (MiniLM=384) | Optional |
| EMBED_MODEL | SentenceTransformer model | Optional |
| LOCALAI_ENDPOINT | LocalAI base URL | Optional |
| OPENAI_API_KEY | Remote key (if not LocalAI) | Optional |
| MODEL_NAME | Chat model for summarization | Optional |
| GOVINFO_API_KEY | govinfo key (rate/coverage) | Recommended |
| OPENSTATES_API_KEY | OpenStates key | Recommended |
| ENABLE_NEO4J | "1" to enable Neo4j features | Optional |
| NEO4J_URI | bolt:// URI | If Neo4j enabled |
| NEO4J_USER | Neo4j user | If Neo4j enabled |
| NEO4J_PASSWORD | Neo4j password | If Neo4j enabled |

## CLI Commands
| Command | Purpose |
|---------|---------|
| --init-db | Initialize PostgreSQL schema |
| --sync-govinfo --govinfo-collections BILLSTATUS,PLAW --govinfo-days 7 | Ingest govinfo |
| --sync-openstates --openstates-states "California,Texas" --openstates-pages 2 | Ingest OpenStates |
| --ingest-local --local-patterns "data/local/**/*.txt" | Ingest local files |
| --embed | Compute embeddings for new sections |
| --one-shot-query "text" --plain | Single query from CLI |
| --serve --port 8090 | Launch API server |
| --export-bloom | Export Bloom perspective (if Neo4j enabled) |

## Data Model (PostgreSQL)
- documents(id, ext_id, bill_id, title, jurisdiction, provenance JSONB)
- sections(id, document_id, section_no, text)
- embeddings(section_id, embedding vector, model)
- bills(bill_id, title, raw_text, jurisdiction)
- politicians(politician_id, name, party, region) [placeholder future ingestion]
- votes(vote_id, bill_id, vote_date, meta)
- vote_choices(vote_id, politician_id, choice)

## Extending
- Add dedicated sponsor/vote ingestion (e.g., ProPublica Congress API).
- Add municipal scraping adaptors (city council minutes).
- Add advanced RAG synthesis combining top-K sections into summarizer prompt.
- Add scheduler (cron job or lightweight loop container) for periodic ingestion.

## Limitations
- Parsing is heuristic; legislative XML variety requires schema-specific parsing for best fidelity.
- Plain-language summaries are not legal advice.
- Without fork metadata (not retrieved), no direct integration assumptions included.

## License
Adapt freely. Verify any external data source terms.
