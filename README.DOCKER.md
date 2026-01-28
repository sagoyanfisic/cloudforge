# CloudForge Docker Setup

## Prerequisites

- Docker Desktop installed (https://www.docker.com/products/docker-desktop)
- Docker Compose installed (included with Docker Desktop)
- GOOGLE_API_KEY from Google AI (https://ai.google.dev/)

## Quick Start

### 1. Set Environment Variables

Create or update `.env` file in the project root:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional (customize if needed)
AWS_DIAGRAM_LOG_LEVEL=INFO
AWS_DIAGRAM_OUTPUT_FORMATS=png,pdf,svg
```

### 2. Build and Start Services

```bash
# Using Makefile (recommended)
make build
make up

# Or using docker-compose directly
docker-compose build
docker-compose up -d
```

### 3. Access CloudForge

- **Web UI**: http://localhost:8501
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## Docker Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Docker Compose                             │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────┐        ┌──────────────────────┐    │
│  │  API Service        │        │  UI Service          │    │
│  │  (uvicorn)          │        │  (streamlit)         │    │
│  │  Port: 8000         │        │  Port: 8501          │    │
│  │                     │        │                      │    │
│  │ ├─ FastAPI          │        │ ├─ Streamlit App     │    │
│  │ ├─ LangGraph        │        │ ├─ API Client        │    │
│  │ ├─ Validation       │        │ └─ UI Components     │    │
│  │ └─ Generator        │        │                      │    │
│  └─────────────────────┘        └──────────────────────┘    │
│           ↑                               ↓                   │
│           └───────────────────────────────┘                   │
│                   HTTP Communication                          │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Database Service (Optional)                          │   │
│  │  PostgreSQL 15                                        │   │
│  │  Used for future features: diagram history, users    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Shared Volumes                                       │   │
│  │  ├─ ./diagrams/         (generated diagrams)        │   │
│  │  ├─ ./.env              (environment variables)      │   │
│  │  └─ postgres_data/      (database persistence)       │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

## Common Commands

### Using Makefile (Recommended)

```bash
# View all available commands
make help

# Build images
make build

# Start all services
make up

# View logs
make logs
make logs-api    # API logs only
make logs-ui     # UI logs only

# Stop services
make down

# Clean everything
make clean

# Rebuild and restart
make rebuild

# Open shell in container
make shell-api
make shell-ui

# Check service status
make status
```

### Using Docker Compose Directly

```bash
# Build images
docker-compose build

# Start services (detached mode)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Rebuild without cache
docker-compose build --no-cache
docker-compose up -d
```

## Services

### API Service

- **Image**: Built from `Dockerfile.api`
- **Port**: 8000
- **Base URL**: http://localhost:8000
- **Health Check**: GET /health
- **Environment**:
  - `GOOGLE_API_KEY` - Required for Gemini API
  - `AWS_DIAGRAM_LOG_LEVEL` - Logging level
  - `AWS_DIAGRAM_OUTPUT_FORMATS` - Output formats (png,pdf,svg)

### UI Service

- **Image**: Built from `Dockerfile.ui`
- **Port**: 8501
- **Base URL**: http://localhost:8501
- **Framework**: Streamlit
- **Environment**:
  - `GOOGLE_API_KEY` - Required for API communication
  - `CLOUDFORGE_API_URL` - API endpoint (http://api:8000 internally)

### Database Service (Optional)

- **Image**: postgres:15-alpine
- **Port**: 5432 (internal only)
- **Credentials**: In docker-compose.yml
- **Note**: Currently not used, prepared for future features

## Volumes

### Persistent Volumes

```
diagrams/          - Generated diagram files
postgres_data/     - Database persistence
```

### Environment Files

```
.env               - Environment variables (mounted in containers)
```

## Environment Variables

### Required

```bash
GOOGLE_API_KEY=your_api_key_from_google_ai
```

### Optional

```bash
# API Configuration
AWS_DIAGRAM_LOG_LEVEL=INFO
AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH=/app/diagrams
AWS_DIAGRAM_OUTPUT_FORMATS=png,pdf,svg

# UI Configuration
CLOUDFORGE_API_URL=http://api:8000
```

## Troubleshooting

### API Container Won't Start

```bash
# Check logs
docker-compose logs api

# Common issues:
# 1. GOOGLE_API_KEY not set - add to .env
# 2. Port 8000 in use - stop other services or change port
# 3. Out of memory - increase Docker memory limit
```

### UI Container Won't Connect to API

```bash
# Verify services are running
docker-compose ps

# Check API is healthy
curl http://localhost:8000/health

# Check networking
docker-compose exec ui ping api

# If still failing, restart services
docker-compose down
docker-compose up -d
```

### Files Not Saving to diagrams/

```bash
# Check diagrams volume
ls -la diagrams/

# Verify permissions
docker-compose exec api ls -la /app/diagrams

# Fix if needed
docker-compose exec api chmod 777 /app/diagrams
```

### Port Already in Use

```bash
# Find what's using the port
lsof -i :8000          # API
lsof -i :8501          # UI
lsof -i :5432          # Database

# Kill the process
kill -9 <PID>

# Or change ports in docker-compose.yml
# api: "9000:8000"
# ui: "9501:8501"
```

## Performance Tips

1. **Allocate enough memory**: 4GB+ for smooth operation
2. **Use BuildKit**: `DOCKER_BUILDKIT=1 docker-compose build`
3. **Cache layers**: Avoid frequent rebuilds
4. **Monitor resources**: `docker stats`

## Security Notes

- The `.env` file is mounted into containers - keep secrets secure
- Don't commit `.env` to git (it's in .gitignore)
- Use strong GOOGLE_API_KEY
- Database password is example only - change in production
- CORS is enabled for UI on localhost - restrict in production

## Docker Compose Services

### Health Checks

All services have health checks configured:

```bash
# View health status
docker-compose ps

# Manual health check
curl http://localhost:8000/health
curl http://localhost:8501
```

## Production Deployment

For production, consider:

1. **Use environment secrets**: Docker Secrets or environment variable management
2. **Enable logging drivers**: ELK, Splunk, or CloudWatch
3. **Configure persistent storage**: Mount external volumes
4. **Use load balancer**: nginx or similar for multiple API instances
5. **Enable monitoring**: Prometheus, Grafana, or similar
6. **Set resource limits**: Memory and CPU constraints
7. **Update base images**: Latest Python 3.12 security patches

## Next Steps

1. Run: `make up`
2. Open browser to http://localhost:8501
3. Try example: "IoT sensors with Kinesis, Lambda, and DynamoDB"
4. Check logs: `make logs`
5. Stop when done: `make down`

---

For more information, see:
- `API_AND_UI_GUIDE.md` - API documentation
- `IMPLEMENTATION_SUMMARY.md` - Architecture details
- `README.md` - Project overview

