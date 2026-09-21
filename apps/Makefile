COMPOSE = docker compose -f docker-compose.yml

.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "  Product Management Skill Jev - Apps"
	@echo "  apps/backend/   FastAPI backend"
	@echo "  apps/frontend/  Next.js web portal"
	@echo "  ────────────────────────────────"
	@echo "  make start    Start web portal + API"
	@echo "  make stop     Stop all containers"
	@echo "  make restart  Restart containers"
	@echo "  make logs     Follow logs"
	@echo "  make build    Rebuild images"
	@echo "  make status   Show health"
	@echo ""

start:
	$(COMPOSE) up -d --build
	@echo ""
	@echo "  Web portal: http://localhost:80"
	@echo "  API:        http://localhost:8000"
	@echo ""

stop:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f

build:
	$(COMPOSE) build --no-cache

status:
	$(COMPOSE) ps

.PHONY: help start stop restart logs build status
