# CloudForge

**AI-Powered AWS Architecture Diagrams from Natural Language**

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org)
[![LangChain](https://img.shields.io/badge/LangChain-v0.1.0-orange)](https://python.langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-blueviolet)](https://langchain-ai.github.io/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20UI-red)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Yes-brightgreen)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

CloudForge generates professional AWS architecture diagrams from plain English descriptions. It uses a 2-step workflow: first an AI refines your description, then a LangGraph pipeline produces validated Python code rendered by GraphViz.

---

## Features

- **Description refinement** — paste a brief description, AI enhances it with data flows, layers, and best practices before you approve it
- **LangGraph pipeline** — 5-node state machine: blueprint → AWS MCP enrichment → code → validation → rendering
- **Dynamic imports** — all 1000+ `diagrams` library symbols (AWS, K8S, on-prem, SaaS) are pre-imported; the LLM never needs to write import statements
- **AST validation** — syntax check, security scan, and AWS component whitelist before execution
- **Multiple output formats** — PNG, PDF, SVG
- **REST API + Web UI** — FastAPI backend, Streamlit frontend

---

## Quick Start

### Prerequisites

- Python 3.12+
- [UV](https://astral.sh/uv/) package manager
- GraphViz (`brew install graphviz` / `sudo apt install graphviz`)
- Google API key — get one at <https://ai.google.dev>

### Option 1: Docker Compose (recommended)

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_key

make build
make up
# Web UI: http://localhost:8501
# API docs: http://localhost:8000/docs
```

```bash
make down    # stop
make logs    # tail logs
make rebuild # full rebuild
```

### Option 2: Local (UV)

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_key

uv sync

# Terminal 1 — API
uv run python -m src.presentation.api --port 8000

# Terminal 2 — UI
uv run streamlit run ui/app.py --server.port 8501
```

---

## How It Works

### User workflow

```
1. Enter description   →  "Lambda, API Gateway, DynamoDB"
2. Click Refine        →  AI enhances with data flows and architecture layers
3. Review & approve    →  Edit if needed, then confirm
4. Generate            →  Diagram rendered with validation report
```

### Backend pipeline (LangGraph)

```
description
    │
    ▼
[blueprint]     BlueprintArchitectChain (Gemini)
                Extracts services, relationships → structured JSON
    │
    ▼
[enrich_mcp]    AWS Documentation MCP (optional)
                Adds best practices per service
    │
    ▼
[coder]         DiagramCoderChain (Gemini)
                JSON blueprint → Python diagrams code
    │
    ▼
[validator]     DiagramValidator
                AST parse · security scan · component whitelist
    │
    ▼
[generator]     DiagramGenerator
                Wildcard imports + exec → PNG / PDF / SVG
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/diagrams/refine` | Refine a brief description |
| `POST` | `/v1/diagrams/generate` | Generate diagram from description |
| `GET` | `/v1/diagrams/history` | List recent diagrams |
| `GET` | `/v1/diagrams/{id}` | Get diagram by ID |
| `GET` | `/images/{filename}` | Serve PNG / PDF / SVG |
| `GET` | `/health` | Health check |

Interactive docs available at `http://localhost:8000/docs`.

### Refine a description

```bash
curl -X POST http://localhost:8000/v1/diagrams/refine \
  -H "Content-Type: application/json" \
  -d '{"description": "Lambda, API, DB"}'
```

```json
{
  "success": true,
  "original": "Lambda, API, DB",
  "refined": "API Gateway provides REST entry point...",
  "message": "Description refined successfully"
}
```

### Generate a diagram

```bash
curl -X POST http://localhost:8000/v1/diagrams/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "API Gateway routes requests to Lambda which reads/writes DynamoDB",
    "name": "serverless_api"
  }'
```

---

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | *(required)* | Google Gemini API key |
| `AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH` | `~/.aws_diagrams` | Where diagrams are saved |
| `AWS_DIAGRAM_OUTPUT_FORMATS` | `png,pdf,svg` | Output formats |
| `AWS_DIAGRAM_LOG_LEVEL` | `INFO` | Log verbosity |
| `CLOUDFORGE_DISABLE_AWS_MCP` | `1` | Set to `0` to enable AWS MCP enrichment |
| `CLOUDFORGE_API_URL` | `http://localhost:8000` | API URL used by the Streamlit UI |

---

## Project Structure

```
mcp-aws/
├── src/
│   ├── presentation/
│   │   ├── api.py              # FastAPI app — /refine, /generate, /history
│   │   └── api_models.py       # Pydantic request/response models
│   ├── application/
│   │   └── services.py         # Use-case services + repository pattern
│   ├── infrastructure/
│   │   ├── langchain_chains.py # DescriptionRefinerChain, BlueprintArchitectChain, DiagramCoderChain
│   │   ├── langgraph_pipeline.py # 5-node LangGraph state machine
│   │   ├── generator.py        # Wildcard imports + diagram execution
│   │   ├── validator.py        # AST validation + security scan
│   │   ├── storage.py          # File-based storage with JSON index
│   │   ├── aws_mcp_client.py   # AWS Documentation MCP client (optional)
│   │   ├── mcp_client.py       # MCP direct client
│   │   ├── server.py           # MCP server tools
│   │   ├── config.py           # pydantic-settings configuration
│   │   └── nlp/                # NLP utilities (architect, coder, processor, models)
│   └── domain/
│       └── models.py           # Domain models + exceptions
├── ui/
│   ├── app.py                  # Streamlit 2-step UI
│   └── api_client.py           # HTTP client for the API
├── docker/
│   ├── Dockerfile.api
│   └── Dockerfile.ui
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── .env.example
```

---

## Testing

```bash
# Run all tests
uv run pytest -xvs tests/

# Single file
uv run pytest -xvs tests/test_validator.py

# With coverage
uv run pytest --cov=src --cov-report=html tests/
```

---

## Troubleshooting

**GraphViz not found**
```bash
brew install graphviz        # macOS
sudo apt install graphviz    # Ubuntu/Debian
```

**`diagrams` module not found**
```bash
uv sync
```

**API unreachable from UI**
```bash
curl http://localhost:8000/health
# Verify CLOUDFORGE_API_URL in .env matches the running API address
```

---

## License

MIT — see [LICENSE](LICENSE).
