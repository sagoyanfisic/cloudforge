# 🔥 CloudForge

**AI-Powered AWS Architecture Diagrams with Validation & Persistence**

Transform your cloud infrastructure vision into professional AWS architecture diagrams instantly.

## ✨ What is CloudForge?

CloudForge is an intelligent MCP (Model Context Protocol) server that leverages Claude AI to generate, validate, and persistently store AWS architecture diagrams. It bridges the gap between architectural thinking and visual representation.

### Core Features

🎨 **Diagram Generation**
- Generate AWS architecture diagrams from Python code
- Support for 50+ AWS components (EC2, Lambda, RDS, S3, etc.)
- Multiple output formats: PNG, PDF, SVG

✓ **Intelligent Validation**
- Syntax validation using AST parsing
- AWS component whitelisting
- Relationship analysis
- Security scanning (detects dangerous functions)
- Component counting and statistics

💾 **Persistent Storage**
- Save diagrams with metadata
- Tag-based organization
- Checksum verification
- JSON-based indexing
- Full CRUD operations

🔍 **Multi-Account Architecture Support**
- Hub-and-spoke patterns
- PrivateLink connectivity
- Cross-region deployments
- Centralized monitoring

📊 **Enterprise Ready**
- FastMCP implementation
- Pydantic data validation
- Comprehensive logging
- Docker containerization
- UV package management

## 🚀 Quick Start

### Docker
```bash
docker run -it \
  -v $(pwd)/examples:/app/examples \
  cloudforge:latest \
  python -m src
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python -m src

# Run examples
python examples/serverless_app.py
python examples/aws_hub_spoke.py
```

## 📋 Architecture

```
cloudforge/
├── src/
│   ├── __init__.py          # Package & entry point
│   ├── server.py            # FastMCP server implementation
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic data models
│   ├── validator.py         # Diagram validation logic
│   ├── generator.py         # Diagram generation engine
│   └── storage.py           # Persistent storage layer
├── examples/                # Ready-to-use diagram examples
│   ├── serverless_app.py
│   ├── microservices.py
│   ├── multi_region.py
│   ├── aws_hub_spoke.py
│   └── multi_account_thanos.py
├── tests/                   # Test suite
├── Dockerfile              # Docker configuration with UV
├── pyproject.toml          # Project metadata
└── uv.lock                 # Dependency lock file
```

## 🎯 Use Cases

- **Architects**: Rapidly prototype and document cloud architectures
- **DevOps Teams**: Maintain accurate infrastructure diagrams
- **Organizations**: Implement governance with validated architecture patterns
- **Learning**: Understand AWS best practices through visual examples
- **Documentation**: Generate diagrams directly from infrastructure-as-code

## 🔧 MCP Tools

CloudForge exposes 5 powerful MCP tools:

### 1. `generate_diagram`
Generate an AWS architecture diagram from Python code
```python
generate_diagram(
    code: str,              # Python diagram code
    name: str,              # Diagram name
    description: str = "",  # Optional description
    validate: bool = True   # Validate before generating
)
```

### 2. `validate_diagram`
Validate diagram code for syntax and security
```python
validate_diagram(code: str)
```

### 3. `list_diagrams`
List all saved diagrams with metadata
```python
list_diagrams(tag: str = None)
```

### 4. `get_diagram`
Retrieve a specific diagram by ID
```python
get_diagram(diagram_id: str)
```

### 5. `delete_diagram`
Delete a saved diagram
```python
delete_diagram(diagram_id: str)
```

## 📦 Technology Stack

- **FastMCP**: Model Context Protocol server framework
- **Diagrams**: Python DSL for cloud architecture diagrams
- **Pydantic**: Data validation using Python type hints
- **GraphViz**: Diagram rendering engine
- **UV**: Fast Python package manager
- **Docker**: Containerization with python:3.12-slim

## 📊 Example: Hub-and-Spoke Architecture

CloudForge includes examples for complex multi-account AWS architectures:

```
Management Account (HUB)
├── Central Monitoring (Lambda)
├── Metrics Storage (S3)
└── Logs Storage (S3)
    └── PrivateLink Endpoints
        ├── Project OZ (Dev/Stg/Prod)
        ├── Project ERPNext (Dev/Stg/Prod)
        └── Project Backend (Dev/Stg/Prod)

Development Account (SPOKE)
├── Metrics Collector (Lambda)
└── Workloads (ECS/EC2)

Staging Account (SPOKE)
├── Metrics Collector (Lambda)
└── Workloads (ECS/EC2)

Production Account (SPOKE)
├── Metrics Collector (Lambda)
└── Workloads (ECS/EC2)
```

## 🔒 Security

- Input validation on all diagram code
- Dangerous function detection (exec, eval, file operations)
- Component whitelisting (only approved AWS services)
- Non-root Docker execution (uid/gid 1000)
- SHA256 checksum verification

## 📈 Performance

- **Build Time**: ~2 minutes (with caching)
- **Diagram Generation**: <5 seconds per diagram
- **Storage**: Efficient JSON indexing
- **Concurrency**: FastMCP async support

## 🤝 Contributing

CloudForge is built with extensibility in mind. Easy to add:
- New AWS components
- Custom validation rules
- Additional output formats
- New diagram patterns

## 📝 License

MIT License - See LICENSE file

---

**CloudForge** - Forge your cloud architecture with AI ⚡
