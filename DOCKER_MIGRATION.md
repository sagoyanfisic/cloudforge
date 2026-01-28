# Docker Migration Summary

## What Changed

### From Shell Scripts → Docker Compose

Previously, CloudForge was started with shell scripts:
- `scripts/start_api.sh`
- `scripts/start_ui.sh`
- `scripts/start_all.sh`

Now everything runs with Docker:
```bash
make build
make up
```

### Key Improvements

1. **Environment Variable Loading**
   - `.env` file is now automatically loaded
   - GOOGLE_API_KEY is properly validated
   - Better error messages when credentials are missing

2. **Docker Containers**
   - Separate API container (Dockerfile.api)
   - Separate UI container (Dockerfile.ui)
   - Optional PostgreSQL database (prepared for future use)

3. **Easy Management**
   - Makefile with convenient commands
   - Health checks for all services
   - Comprehensive logging
   - Persistent volumes for diagrams

4. **Configuration**
   - All settings via `.env` file
   - Docker Compose orchestration
   - Network isolation between services

## Files Added

```
Dockerfile.api        - API service with FastAPI
Dockerfile.ui         - UI service with Streamlit
docker-compose.yml    - Service orchestration
Makefile              - Convenient commands
README.DOCKER.md      - Complete Docker guide
.dockerignore         - Build optimization
```

## Files Modified

```
src/infrastructure/config.py        - Auto-load .env
src/infrastructure/langchain_chains.py - Validate API key
```

## Files Deleted

```
scripts/start_api.sh
scripts/start_ui.sh
scripts/start_all.sh
```

## Quick Start

```bash
# 1. Set API key
echo "GOOGLE_API_KEY=your_key" > .env

# 2. Build and start
make build
make up

# 3. Open browser
# API: http://localhost:8000
# UI: http://localhost:8501

# 4. Stop services
make down
```

## Troubleshooting

### Issue: ⚠️ LangGraph Pipeline not available

**Solution**: Ensure GOOGLE_API_KEY is set in `.env`:

```bash
# Check if set
echo $GOOGLE_API_KEY

# If empty, set it
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# Rebuild and restart
make rebuild
```

### Issue: Port already in use

```bash
# Find what's using the port
lsof -i :8000
lsof -i :8501

# Kill the process
kill -9 <PID>

# Restart containers
make down
make up
```

### Issue: UI can't connect to API

```bash
# Check API is running
docker-compose ps

# Check API health
curl http://localhost:8000/health

# View API logs
make logs-api

# Restart services
make restart
```

## Make Commands Reference

```
make help       - Show all commands
make build      - Build Docker images
make up         - Start services
make down       - Stop services
make logs       - View all logs
make logs-api   - View API logs
make logs-ui    - View UI logs
make clean      - Remove containers and volumes
make rebuild    - Rebuild and restart
make status     - Check service status
make shell-api  - Open shell in API container
make shell-ui   - Open shell in UI container
```

## Environment Variables

### Required

```bash
GOOGLE_API_KEY=your_api_key_from_google_ai
```

### Optional

```bash
# Logging
AWS_DIAGRAM_LOG_LEVEL=INFO

# Output formats
AWS_DIAGRAM_OUTPUT_FORMATS=png,pdf,svg

# Storage path (inside container)
AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH=/app/diagrams
```

## Service Ports

- **API**: http://localhost:8000
  - Health: http://localhost:8000/health
  - Docs: http://localhost:8000/docs (Swagger)

- **UI**: http://localhost:8501
  - Main interface for diagram generation

- **Database**: localhost:5432 (internal only)
  - Not exposed outside Docker network

## Documentation

- `README.DOCKER.md` - Comprehensive Docker guide
- `Makefile` - All available commands
- `docker-compose.yml` - Service configuration

## Migration Benefits

✅ **Consistency**: Same environment for development and production
✅ **Isolation**: Services run in isolated containers
✅ **Scalability**: Easy to add more services or replicas
✅ **Persistence**: Diagrams survive container restarts
✅ **Health Checks**: Automatic monitoring and recovery
✅ **Easy Management**: Simple make commands
✅ **Production-Ready**: Follows Docker best practices

## Next Steps

1. Run `make build`
2. Run `make up`
3. Open http://localhost:8501
4. Try generating a diagram!

---

For more details, see README.DOCKER.md
