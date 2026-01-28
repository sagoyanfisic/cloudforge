.PHONY: help build up down logs clean rebuild test

help:
	@echo "CloudForge Docker Commands"
	@echo "========================="
	@echo "make build       - Build Docker images"
	@echo "make up          - Start all services"
	@echo "make down        - Stop all services"
	@echo "make rebuild     - Rebuild images and restart"
	@echo "make logs        - View logs from all services"
	@echo "make logs-api    - View API logs"
	@echo "make logs-ui     - View UI logs"
	@echo "make clean       - Remove containers and volumes"
	@echo "make test        - Run tests in container"
	@echo "make shell-api   - Open shell in API container"
	@echo "make shell-ui    - Open shell in UI container"
	@echo ""
	@echo "Quick start: make up"
	@echo "Then open: http://localhost:8501"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "✅ CloudForge is starting..."
	@echo "📡 API: http://localhost:8000"
	@echo "🎨 UI: http://localhost:8501"
	@sleep 5
	docker-compose logs

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-api:
	docker-compose logs -f api

logs-ui:
	docker-compose logs -f ui

clean:
	docker-compose down -v
	rm -rf diagrams/
	@echo "✅ Cleaned up"

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ Rebuilt and restarted"

test:
	docker-compose exec api pytest tests/

shell-api:
	docker-compose exec api bash

shell-ui:
	docker-compose exec ui bash

status:
	docker-compose ps

pull-logs:
	docker-compose logs --tail=50

