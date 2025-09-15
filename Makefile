# ==============================================================================
# Makefile for Project Sentinel
# ==============================================================================
# This file provides simple, memorable commands to manage the complex
# Docker Compose stack for the Political Intelligence Platform.
#
# Usage:
#   make up         - Start all services in detached mode.
#   make down       - Stop and remove all services and volumes.
#   make logs       - Follow the logs of all services.
#   make logs-agent - Follow the logs of just the agentic-kg service.
#   make rebuild    - Rebuild the images and restart the services.
# ==============================================================================

# Use docker compose v2 syntax
COMPOSE := docker compose

# Default compose files
COMPOSE_FILES := -f docker-compose.yml

# Check for an override file and include it if it exists
ifneq (,$(wildcard docker-compose.override.yml))
    COMPOSE_FILES += -f docker-compose.override.yml
endif

.PHONY: up down logs logs-agent rebuild stop ps

# Start all services in the background
up:
	@echo "🚀 Starting all Project Sentinel services..."
	$(COMPOSE) $(COMPOSE_FILES) up --build -d

# Stop and remove containers, networks, and volumes
down:
	@echo "🛑 Stopping and removing all services and data..."
	$(COMPOSE) $(COMPOSE_FILES) down -v

# Stop containers without removing them
stop:
	@echo "✋ Stopping all services..."
	$(COMPOSE) $(COMPOSE_FILES) stop

# Follow logs from all services
logs:
	@echo "📜 Tailing logs from all services..."
	$(COMPOSE) $(COMPOSE_FILES) logs -f

# Follow logs for a specific service
logs-agent:
	@echo "📜 Tailing logs for the agentic-kg service..."
	$(COMPOSE) $(COMPOSE_FILES) logs -f agentic-kg

# Force a rebuild of the service images
rebuild:
	@echo "🛠️  Forcing a rebuild of all service images..."
	$(COMPOSE) $(COMPOSE_FILES) up --build -d --force-recreate

# List running containers
ps:
	@echo "📋 Listing running services..."
	$(COMPOSE) $(COMPOSE_FILES) ps
