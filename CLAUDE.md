# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CloudForge** — AI-powered AWS architecture diagram generator. Transforms plain English descriptions into rendered diagrams (PNG/PDF/SVG) via a 2-step workflow: description refinement → diagram generation using LangGraph + Google Gemini 2.5-Flash.

## Common Commands

**Package manager:** `uv` (not pip or poetry)

```bash
uv sync                          # Install dependencies
uv run pytest -xvs tests/        # Run all tests
uv run pytest -xvs tests/test_validator.py  # Single test file
uv run pytest --cov=src --cov-report=html   # With coverage

# Local dev (two terminals)
uv run python -m src.presentation.api --port 8000
uv run streamlit run ui/app.py --server.port 8501
```

**Docker (recommended):**
```bash
cp .env.example .env             # Set GOOGLE_API_KEY in .env first
make build && make up            # Build and start services
make logs                        # View all logs
make logs-api / make logs-ui     # Per-service logs
make test                        # Run pytest in container
make rebuild                     # Full rebuild
make clean                       # Remove containers + volumes
```

**Code quality:**
```bash
uv run black src/ ui/ --line-length 100
uv run ruff check src/ ui/
uv run mypy src/
```

## Architecture

Clean Architecture with 4 layers:

```
Presentation (src/presentation/)   → FastAPI on :8000
Application  (src/application/)    → Service + Repository pattern
Domain       (src/domain/)         → Business models + exceptions
Infrastructure (src/infrastructure/) → LangChain, LangGraph, storage, validation
```

Streamlit UI (`ui/`) is a separate frontend that calls the FastAPI backend via `ui/api_client.py`.

### Key Data Flow

1. User submits brief description → `POST /v1/diagrams/refine` (DescriptionRefinerChain)
2. User approves refined description → `POST /v1/diagrams/generate`
3. LangGraph pipeline executes 5 nodes:
   - `blueprint_node` — Extract AWS services/relationships (BlueprintArchitectChain)
   - `enrich_mcp_node` — Optionally enrich via AWS MCP (disabled by default)
   - `coder_node` — Generate Python `diagrams` library code (DiagramCoderChain)
   - `validator_node` — AST parse + security scan (DiagramValidator)
   - `generator_node` — Execute code → render image (DiagramGenerator)
4. Images served at `GET /images/{filename}`

### Critical Files

| File | Purpose |
|------|---------|
| `src/infrastructure/langgraph_pipeline.py` | 5-node LangGraph state machine with retry logic |
| `src/infrastructure/langchain_chains.py` | Three Gemini 2.5-Flash chains (refiner, architect, coder) |
| `src/infrastructure/validator.py` | AST validation + security scanning of generated code |
| `src/infrastructure/generator.py` | Executes validated Python code to produce diagrams |
| `src/domain/models.py` | Domain models, aggregates, `GenerationDomainError`, `ValidationDomainError` |
| `src/infrastructure/config.py` | All settings via pydantic-settings (env prefix: `AWS_DIAGRAM_` or `CLOUDFORGE_`) |
| `ui/app.py` | 2-step Streamlit UI (refine → review → generate) |

## Required Environment Variables

```bash
GOOGLE_API_KEY=...              # Required — Google Gemini API key
CLOUDFORGE_DISABLE_AWS_MCP=1    # Set to 0 to enable AWS Documentation MCP enrichment
```

Storage defaults to `~/.cloudforge/diagrams`. Output formats: `png,pdf,svg`. See `.env.example` for all options.

## Technology Stack

- **LLM:** Google Gemini 2.5-Flash via `langchain-google-genai`
- **Orchestration:** LangGraph (state machine with retry)
- **Diagram rendering:** `diagrams` library + GraphViz (system dep)
- **API:** FastAPI + Uvicorn
- **Frontend:** Streamlit
- **Validation:** Pydantic v2 + pydantic-settings
- **Protocol:** MCP (Model Context Protocol) for optional AWS docs enrichment

## Code Style

- Line length: 100 characters (black)
- Linting: ruff (rules E, F, W, I)
- Type checking: mypy strict mode
- Python: 3.10+ (3.12 in Docker)
