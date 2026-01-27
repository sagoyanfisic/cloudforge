# CloudForge API and Web UI Guide

## Overview

CloudForge now includes a complete REST API and web UI for generating AWS architecture diagrams from natural language descriptions.

### Architecture

```
[User Browser]
      ↓ HTTP
[Streamlit UI] ←→ [FastAPI Server] → [LangGraph Pipeline]
                      ↓
                [Storage + Images]
```

## Quick Start

### Option 1: Start Both Services

```bash
./scripts/start_all.sh
```

Then open your browser to **http://localhost:8501**

### Option 2: Start Services Separately

**Terminal 1 - Start API:**
```bash
./scripts/start_api.sh
# API listens on http://localhost:8000
```

**Terminal 2 - Start UI:**
```bash
./scripts/start_ui.sh
# UI opens at http://localhost:8501
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Generate Diagram
```bash
curl -X POST http://localhost:8000/v1/diagrams/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "IoT system with Kinesis, Lambda, and DynamoDB",
    "name": "iot_pipeline"
  }'
```

**Response includes:**
- `blueprint`: Technical architecture blueprint
- `code`: Generated Python code
- `validation`: AST validation results (errors, warnings, component count, relationships)
- `output_files`: Paths to PNG, PDF, SVG files

### List Diagrams
```bash
curl http://localhost:8000/v1/diagrams
```

### Get Diagram Details
```bash
curl http://localhost:8000/v1/diagrams/{diagram_id}
```

### Delete Diagram
```bash
curl -X DELETE http://localhost:8000/v1/diagrams/{diagram_id}
```

### Serve Image
```bash
curl http://localhost:8000/images/{filename}
```

## Web UI Features

### Main Editor
- **Description Input**: Enter natural language architecture description
- **Diagram Name**: Provide a name for your diagram
- **Generate Button**: Trigger diagram generation (uses LangGraph with auto-retry)

### Results Display

#### Diagram Image
- Compact thumbnail view by default
- Expandable button for full-size viewing
- Supports PNG, PDF, and SVG formats

#### Validation Panel
Shows complete AST validation results:
- **Status**: Pass/Fail indicator
- **Metrics**: Component count, relationship count
- **Errors**: Any syntax or validation errors
- **Warnings**: Any warnings or security concerns

#### Technical Blueprint
Expandable panel showing:
- Architecture title and description
- List of AWS services (nodes)
- Service connections (relationships)

#### Generated Code
Expandable panel showing the Python code using diagrams DSL

### History Panel
- Lists recent saved diagrams
- View full details of any diagram
- Delete diagrams
- Quick access to previous work

## Environment Variables

```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional API Configuration
CLOUDFORGE_API_HOST=0.0.0.0          # API listen address
CLOUDFORGE_API_PORT=8000              # API listen port
CLOUDFORGE_API_URL=http://localhost:8000  # API URL for UI

# Optional UI Configuration
CLOUDFORGE_UI_HOST=localhost           # UI listen address
CLOUDFORGE_UI_PORT=8501               # UI listen port
```

## Configuration

### Storage Path
Default: `~/.cloudforge/diagrams/`

Generated diagrams are stored with:
- `{id}.png` - PNG image
- `{id}.pdf` - PDF document
- `{id}.svg` - SVG vector graphic
- `{id}.py` - Source Python code
- `{id}.json` - Metadata

### API Configuration

Edit `src/infrastructure/config.py` to customize:
- Output formats
- Storage path
- Validation limits
- Logging level

## Common Use Cases

### 1. Generate Simple API Architecture
```
Description: "Simple REST API with Lambda, DynamoDB, and API Gateway"
Name: "rest_api"
```

### 2. Generate IoT System
```
Description: "IoT sensors send data to Kinesis, Lambda processes it, stores in DynamoDB, and CloudWatch monitors"
Name: "iot_system"
```

### 3. Generate Microservices
```
Description: "Microservices with ECS containers, RDS database, SQS queue, and ALB load balancer"
Name: "microservices"
```

## Troubleshooting

### API Connection Failed
- Ensure API is running: `./scripts/start_api.sh`
- Check API is accessible: `curl http://localhost:8000/health`
- Verify GOOGLE_API_KEY is set: `echo $GOOGLE_API_KEY`

### LangGraph Pipeline Not Available
- Set GOOGLE_API_KEY: `export GOOGLE_API_KEY=your_key`
- Restart API: `./scripts/start_api.sh`

### Images Not Loading
- Check storage path exists: `ls ~/.cloudforge/diagrams/`
- Verify API is serving images: `curl http://localhost:8000/images/test.png`

### UI Slow or Timeout
- Increase timeout: Edit `ui/api_client.py` timeout values
- Check API logs: `./scripts/start_api.sh` output
- Verify network connectivity: `curl http://localhost:8000/health`

## Development

### Run Tests
```bash
pytest tests/
```

### Type Checking
```bash
mypy src/
```

### Code Formatting
```bash
black src/ ui/
```

### Linting
```bash
ruff check src/ ui/
```

## Architecture Details

### API Layer (`src/api.py`)
- FastAPI application with CORS enabled
- Integrates with LangGraph pipeline
- Manages file storage and serving
- Validation and error handling

### Models (`src/api_models.py`)
- Pydantic models for type-safe API
- Request/response schemas
- Validation data structures

### UI Client (`ui/api_client.py`)
- HTTP client for API communication
- Handles timeouts and errors
- Image URL management

### Streamlit UI (`ui/app.py`)
- Two-column layout (main + sidebar)
- Session state management
- Responsive component rendering
- Validation panel with error/warning details

### LangGraph Pipeline
- Orchestrates diagram generation
- Auto-retry on failures
- Structured output parsing
- Complete error handling

## Security

### File Serving
- Filename validation (no path traversal)
- File extension validation (only .png, .pdf, .svg)
- Safe path resolution

### API
- CORS enabled for localhost
- Input validation via Pydantic
- No exposed secrets in responses
- Comprehensive error handling

## Performance

- **Generation Time**: 5-15 seconds (with retries)
- **Validation**: <1 second
- **File Serving**: <100ms
- **UI Response**: <500ms

## Future Enhancements

- [ ] User authentication
- [ ] Diagram sharing/export
- [ ] Custom styling options
- [ ] Batch generation
- [ ] Diagram versioning
- [ ] Collaboration features

## Support

For issues or questions:
1. Check API logs: `./scripts/start_api.sh`
2. Check UI logs: Streamlit console output
3. Verify GOOGLE_API_KEY is set
4. Review LangGraph pipeline configuration

