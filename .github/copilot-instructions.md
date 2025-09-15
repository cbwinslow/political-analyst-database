# Political Intelligence Platform

Political Intelligence Platform is a comprehensive, self-hosted platform for the automated ingestion, analysis, and visualization of political and legislative documents. This platform leverages a suite of modern, open-source tools to create a powerful analytical engine using Docker containers for PostgreSQL, Neo4j, LocalAI, Ollama, and other services.

Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.

## Working Effectively

- Bootstrap, build, and test the repository:
  - `cp .env.example .env` -- Copy environment template
  - `docker --version && docker compose version` -- Verify Docker is installed (requires Docker 28+ and Compose v2)
  - `docker compose config` -- Validate configuration (should complete in <5 seconds)
  - `make up` -- Start all services. NEVER CANCEL: Takes 2-3 minutes to complete. Set timeout to 5+ minutes.
  - `docker compose ps` -- Check service status after startup
  - `sleep 60 && docker compose ps` -- Wait for services to become healthy (PostgreSQL, Neo4j take 30-60 seconds)

- Install Python dependencies:
  - `pip3 install -r requirements-crawler.txt` -- Install crawler dependencies (takes ~45 seconds)
  - `pip3 install psycopg2-binary neo4j requests` -- Additional dependencies for testing

- Test the platform:
  - Test database: `docker exec postgres_db psql -U poladmin -d policydocs -c "\dt legislative.*"`
  - Test Neo4j: `curl -u neo4j:please_change_me_to_a_secure_password http://localhost:7474/db/data/`
  - Test LocalAI: `curl http://localhost:8080/v1/models`
  - Test Ollama: `curl http://localhost:11434/api/tags`

## Build and Deploy Commands

- **Full stack deployment**: 
  - `make up` -- NEVER CANCEL: Takes 2-3 minutes total. Set timeout to 5+ minutes.
  - Image pulling: ~60-90 seconds
  - Service startup: ~60-90 seconds
  - Health checks: Additional 30-60 seconds for databases

- **Core services only**:
  - `docker compose up -d postgres neo4j ollama localai` -- NEVER CANCEL: Takes 30-60 seconds. Set timeout to 2+ minutes.

- **Service management**:
  - `make down` -- Stop and remove all services and data volumes
  - `make stop` -- Stop services without removing data
  - `make logs` -- View logs from all services
  - `make ps` -- List running services

## Validation

- **ALWAYS run validation after making changes**:
  - Create test script in `/tmp/test_platform.py` and run `python3 /tmp/test_platform.py`
  - Verify PostgreSQL schema: `docker exec postgres_db psql -U poladmin -d policydocs -c "SELECT COUNT(*) FROM legislative.legislators;"`
  - Test Python scripts: `python3 doc_scout.py` (will show connection errors if services not running)

- **Database validation**:
  - PostgreSQL should have `legislative` schema with 5 tables (bills, committees, legislator_votes, legislators, votes)
  - pgvector extension should be installed
  - Neo4j should respond to basic queries

- **Service accessibility**:
  - PostgreSQL: `localhost:5432`
  - Neo4j Browser: `http://localhost:7474` (user: neo4j, password from .env)
  - LocalAI API: `http://localhost:8080`
  - Ollama API: `http://localhost:11434`
  - OpenWebUI: `http://localhost:8090`
  - Langfuse: `http://localhost:3002`

## Environment Setup

- **Required files**:
  - `.env` -- Copy from `.env.example` and update passwords
  - `docker-compose.yml` -- Main orchestration file (copied from `docker-stack.yml`)
  - `kong/kong.yml` -- API gateway configuration
  - `init_db/01-init.sql` -- Database initialization script
  - `prometheus/prometheus.yml` -- Monitoring configuration

- **Directory structure**:
  ```
  ├── .env                    # Environment variables
  ├── docker-compose.yml      # Main Docker Compose configuration
  ├── Makefile               # Helper commands
  ├── kong/kong.yml          # API gateway routes
  ├── init_db/01-init.sql    # Database schema
  ├── prometheus/prometheus.yml # Monitoring config
  └── Python scripts (*.py)  # Analysis and crawler services
  ```

## Common Tasks

- **Starting fresh environment**:
  ```bash
  make down  # Clean slate
  cp .env.example .env  # Reset environment
  make up  # NEVER CANCEL: 2-3 minutes
  sleep 60 && docker compose ps  # Verify health
  ```

- **Python development**:
  - Scripts expect services to be running: `make up` first
  - Test connections before running analysis scripts
  - Database schema is automatically created on first startup

- **Troubleshooting**:
  - Check service logs: `make logs-agent` or `docker compose logs [service]`
  - Verify environment: `docker compose config`
  - Test connectivity: Run validation script in `/tmp/`
  - Common issues: Services not healthy (wait longer), port conflicts (check `docker compose ps`)

## Known Issues and Limitations

- **Service timing**: PostgreSQL and Neo4j require 30-60 seconds to become fully healthy
- **Image issues**: Some services may fail to start if images are corrupted - run `docker compose pull` to refresh
- **AI Models**: LocalAI and Ollama start with no models - this is normal, models are downloaded separately
- **Configuration**: Kong expects agentic-kg, crawler, and frontend services that are not defined in the main docker-compose.yml

## Setup Scripts

- `setup_political_ai_stack(1).sh` and `setup_political_ai_stack(2).sh` generate a complete standalone stack
- Generated stack is simpler than the main repository stack
- Run time: ~13ms to generate files
- Generated stack should be tested separately from main repository

## Project Structure

The repository contains:
- **Docker infrastructure**: Complete multi-service stack with databases, AI services, monitoring
- **Python services**: Analysis agents, crawlers, knowledge graph builders
- **Data models**: Pydantic schemas for political entities, bills, legislators
- **Setup automation**: Scripts to generate complete deployable stacks
- **Configuration**: Environment templates, API gateway routes, database schemas

Always build and test the Docker stack before making changes. The platform is designed to work as a complete ecosystem with interdependent services.