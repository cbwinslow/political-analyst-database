#!/bin/bash
# This script prepares the environment for the first launch of Project Sentinel.

set -e

echo "--- Project Sentinel Environment Setup ---"

# List of directories required by docker-compose volumes
DIRECTORIES=(
  "postgres_data"
  "neo4j_data"
  "neo4j_plugins"
  "qdrant_data"
  "n8n_data"
  "localai_models"
  "minio_data"
  "kong_data"
  "grafana_data"
  "loki_data"
  "prometheus_data"
  "agentic_kg/data"
  "crawler/data"
)

echo "Creating necessary data directories..."

for dir in "${DIRECTORIES[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
    echo "  - Created ./${dir}"
  else
    echo "  - Directory ./${dir} already exists."
  fi
done

# Create .env file from example if it doesn't exist
if [ ! -f ".env" ]; then
  echo "\nCreating .env file from .env.example..."
  cp .env.example .env
  echo "  - .env file created successfully."
  echo "\nIMPORTANT: Please open the '.env' file now and fill in any required API keys or secrets."
else
  echo "\n.env file already exists. Skipping creation."
fi

echo "\n--- Setup Complete ---"
echo "You are now ready to launch the stack."
echo "1. (If needed) Edit the .env file with your custom secrets."
echo "2. Run 'make up' to start all services."
