# 🔥 CloudForge

**AI-Powered AWS Architecture Diagrams with Natural Language Processing, AWS MCP Integration, Smart Refinement & Validation**

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Yes-brightgreen)](https://www.docker.com)
[![LangChain](https://img.shields.io/badge/LangChain-v0.1.0-orange)](https://python.langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-blueviolet)](https://langchain-ai.github.io/langgraph)
[![AWS MCP](https://img.shields.io/badge/AWS%20MCP-Integration-FF9900)](https://modelcontextprotocol.io)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20UI-red)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

CloudForge is an **AI-powered platform that generates professional AWS architecture diagrams from natural language descriptions**. Featuring a unique 2-step workflow with AI-powered description refinement, AWS best practices integration, and comprehensive validation.

## ✨ Key Features

### 🤖 Smart Natural Language Processing
- **Describe in plain English**: "Lambda, API Gateway, DynamoDB" → Auto-enhanced to detailed architecture
- **LangChain + Gemini AI**: Advanced NLP pipeline with auto-retry and structured output
- **LangGraph Orchestration**: State machine for reliable multi-step generation with 5 specialized nodes
- **Blueprint Generation**: Extracts services, relationships, and architecture patterns
- **AWS MCP Integration**: Consults AWS Documentation MCP for best practices enrichment

### 🔧 Intelligent Description Refinement (NEW!)
- **Step 1: Refine Prompt** (Optional, user-controlled)
  - User enters brief or vague description
  - AI enhances with architectural details, data flows, technical context
  - User can review and edit before generation

- **Step 2: Review & Approve**
  - Side-by-side view of original vs refined description
  - User has full control and can edit
  - Prevents AI hallucination by requiring approval

- **Step 3: Generate Diagram**
  - Uses only user-approved description
  - Full confidence in what LLM will generate

### 📚 AWS Best Practices Integration
- **Automatic Enrichment**: Detects AWS services (Lambda, RDS, DynamoDB, etc.)
- **AWS Documentation MCP**: Queries official AWS documentation for each service
- **Best Practices Injection**: Incorporates recommendations into code generation
- **Graceful Fallback**: Works seamlessly even if MCP unavailable

### 🎨 Professional Diagrams
- **Auto-Generated Visuals**: Color-coded by environment (production=red, staging=orange, dev=blue)
- **Organized Clusters**: Services grouped by category (Compute, Database, Network, Storage)
- **Dynamic Imports**: All 1000+ diagrams classes available (AWS, K8S, on-prem, generic, SaaS)
- **Edge Labels**: Connection types automatically labeled (triggers, reads_writes, forwards)
- **Multiple Formats**: PNG, PDF, SVG output
- **Production-Ready**: Publication quality with GraphViz rendering

### ✓ Intelligent Validation
- **Python AST Parsing**: Syntax validation of generated code
- **Security Scanning**: Detects dangerous functions and patterns
- **Component Whitelisting**: Validates 50+ AWS services
- **Relationship Analysis**: Ensures logical architecture patterns
- **Comprehensive Reporting**: Errors, warnings, and component metrics

### 💾 Persistent Storage
- **Diagram Management**: Save, retrieve, and organize diagrams
- **Metadata Tracking**: Created date, tags, environment, service categories
- **SHA256 Verification**: File integrity checking
- **JSON Indexing**: Fast retrieval and filtering
- **Full CRUD Operations**: List, get, delete diagrams

### 🚀 Full-Stack Architecture
- **FastAPI Backend**: REST API with `/refine` and `/generate` endpoints
- **Streamlit Web UI**: Interactive 2-step workflow interface
- **Docker Compose**: Complete local development and deployment
- **LangChain Chains**: Specialized processing for blueprint and code generation
- **Environment Detection**: Automatic production/staging/dev classification

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- GraphViz (for diagram rendering)
- Docker & Docker Compose (recommended)
- Google API Key (for Gemini AI) - get it at https://ai.google.dev

### Option 1: Docker Compose (Recommended)

**Fastest way to get started:**

```bash
# Set API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# Build and start services
make build
make up

# Access the UI
# Web UI: http://localhost:8501
# API Docs: http://localhost:8000/docs
```

**Stop services:**
```bash
make down
```

### Option 2: Local Development

```bash
# Install GraphViz
brew install graphviz          # macOS
# sudo apt install graphviz    # Ubuntu/Debian

# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
cd /path/to/mcp-aws
uv sync

# Set API key
export GOOGLE_API_KEY="your_api_key_here"

# Run API server
uv run python -m src.presentation.api --port 8000

# In another terminal, run Streamlit UI
streamlit run ui/app.py --server.port 8501
```

### Option 3: Docker Direct

```bash
# Build image
docker build -t cloudforge:latest .

# Run container with API key
docker run -e GOOGLE_API_KEY="your_key" -p 8000:8000 cloudforge:latest
```

## 📖 How It Works

### 2-Step Workflow (User-Centric)

```
┌─────────────────────────────────────┐
│ STEP 1: Describe Architecture       │
│ ┌─────────────────────────────────┐ │
│ │ Enter brief description:        │ │
│ │ "Lambda, API, DB"              │ │
│ └─────────────────────────────────┘ │
│              ↓                       │
│   [🔧 Refine Prompt Button]        │
└─────────────────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ STEP 2: Review & Approve           │
│ ┌─────────────────────────────────┐ │
│ │ 📋 Original:                    │ │
│ │ "Lambda, API, DB"              │ │
│ │                                 │ │
│ │ 🔄 Refined (AI Enhanced):      │ │
│ │ "API Gateway routes HTTP...    │ │
│ │  Lambda functions process...   │ │
│ │  DynamoDB persists data..."   │ │
│ │                                 │ │
│ │ [✏️ Edit] [✅ Looks Good!]    │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
             ↓
┌─────────────────────────────────────┐
│ STEP 3: Generate & View Results    │
│ ┌─────────────────────────────────┐ │
│ │    [🎨 Architecture Diagram]   │ │
│ │                                 │ │
│ │   [📋 Blueprint] [💻 Code]     │ │
│ │   [✔️ Validation] [📁 Files]   │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### LangGraph Pipeline (Backend Processing)

```
User Refined Description
         ↓
[1] BlueprintArchitectChain (Gemini AI)
    ├─ Analyzes description
    ├─ Extracts services, relationships
    └─ Generates structured JSON blueprint
         ↓
[2] AWS MCP Enrichment Node
    ├─ Detects services in blueprint
    ├─ Queries AWS Documentation MCP
    ├─ Extracts best practices per service
    └─ Enriches blueprint with recommendations
         ↓
[3] DiagramCoderChain (Gemini AI)
    ├─ Converts blueprint to Python code
    ├─ Includes best practices in prompt
    ├─ Adds colors, clusters, styling
    └─ Generates production-ready code
         ↓
[4] Validator (AST Parser)
    ├─ Checks syntax validity
    ├─ Validates AWS components
    ├─ Performs security scanning
    └─ Computes metrics
         ↓
[5] DiagramGenerator (GraphViz + Dynamic Imports)
    ├─ Pre-imports all diagrams symbols
    ├─ Executes Python code
    ├─ Generates PNG/PDF/SVG images
    └─ Stores outputs
         ↓
Generated Diagrams + Validation Report + Blueprint + Code
```

## 📖 Usage Guide

### 1. Two-Step Workflow (Recommended - Web UI)

Open http://localhost:8501

**Step 1: Describe Your Architecture**
```
Enter: "API with Lambda processing and DynamoDB storage"
Click: [🔧 Refine Prompt]
```

**Step 2: Review Refined Description**
```
See AI-enhanced version with:
- Detailed data flows
- Architectural layers
- AWS best practices
Can edit if needed
Click: [✅ Looks Good!]
```

**Step 3: View Generated Diagram**
```
- Full architecture diagram
- Blueprint details
- Generated Python code
- Validation results
- Output files
```

### 2. Refine API Endpoint

```bash
# Step 1: Refine description (optional)
curl -X POST http://localhost:8000/v1/diagrams/refine \
  -H "Content-Type: application/json" \
  -d '{"description":"Lambda, API, DB"}'

# Response:
{
  "success": true,
  "original": "Lambda, API, DB",
  "refined": "API Gateway provides REST entry point...",
  "message": "Description refined successfully"
}
```

### 3. Generate API Endpoint

```bash
# Step 2: Generate diagram with refined description
curl -X POST http://localhost:8000/v1/diagrams/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "API Gateway routes requests to Lambda functions which process and store data in DynamoDB...",
    "name": "serverless_api"
  }'

# Response includes:
# - success: true
# - blueprint: {title, nodes, relationships, best_practices}
# - code: Generated Python diagram code
# - validation: {is_valid, component_count, relationship_count, errors, warnings}
# - output_files: {png, pdf, svg paths}
```

### 4. Full REST API Reference

**List Diagrams:**
```bash
curl http://localhost:8000/v1/diagrams
```

**Get Specific Diagram:**
```bash
curl http://localhost:8000/v1/diagrams/{diagram_id}
```

**Delete Diagram:**
```bash
curl -X DELETE http://localhost:8000/v1/diagrams/{diagram_id}
```

**Serve Image:**
```
http://localhost:8000/images/{filename.png}
```

## 🎯 Key Improvements & Features

### Description Refinement (Smart Enhancement)
- ✅ Detects vague/brief descriptions
- ✅ AI enhances with architectural context
- ✅ User reviews before generation
- ✅ Prevents hallucination via approval
- ✅ Fully editable by user

### AWS MCP Integration
- ✅ Automatic service detection
- ✅ AWS Documentation queries
- ✅ Best practices injection
- ✅ Graceful fallback support
- ✅ Zero extra complexity if unavailable

### Dynamic Imports (All Diagrams Symbols)
- ✅ 1000+ AWS services available
- ✅ K8S, on-prem, generic, SaaS support
- ✅ No manual mapping needed
- ✅ LLM full flexibility
- ✅ Eliminates import errors

### Improved Code Generation
- ✅ Cleaner structure guidance
- ✅ Root-level nodes recommended
- ✅ Cluster usage clarified
- ✅ Better examples provided
- ✅ Fewer retries needed

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
CLOUDFORGE_API_HOST=0.0.0.0
CLOUDFORGE_API_PORT=8000

# UI Configuration
CLOUDFORGE_UI_HOST=localhost
CLOUDFORGE_UI_PORT=8501
CLOUDFORGE_API_URL=http://localhost:8000

# Storage path
AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH=~/.cloudforge/diagrams

# Max file size (MB)
AWS_DIAGRAM_MAX_DIAGRAM_SIZE_MB=100

# Output formats
AWS_DIAGRAM_OUTPUT_FORMATS=png,pdf,svg

# Validation limits
AWS_DIAGRAM_MAX_COMPONENTS=100
AWS_DIAGRAM_MAX_RELATIONSHIPS=200

# Logging level
AWS_DIAGRAM_LOG_LEVEL=INFO

# AWS MCP (optional)
CLOUDFORGE_DISABLE_AWS_MCP=0  # Set to 1 to disable
```

## 📚 Examples

### Example 1: Brief Description (Refinement Needed)

**Input:**
```
"Lambda, API, DB"
```

**AI Refinement:**
```
API Gateway provides REST entry point for users.
Lambda functions process requests with business logic.
DynamoDB persists data with strong consistency.
API Gateway forwards requests to Lambda via event-driven triggers.
Lambda reads/writes to DynamoDB for data persistence.
```

**Generated Diagram:**
- ✅ 3 services properly detected
- ✅ AWS best practices applied
- ✅ Proper connections established
- ✅ Validation passed

### Example 2: Multi-Service Architecture

**Input:**
```
Production serverless API with API Gateway, Lambda processing,
DynamoDB storage, Kinesis streaming, CloudWatch monitoring, and S3 backups
```

**Refinement:**
- Detects: API Gateway, Lambda, DynamoDB, Kinesis, CloudWatch, S3
- Adds: Data flow details, layer organization, best practices
- Suggests: Security considerations, monitoring strategy

**Generated Diagram Includes:**
- ✅ 6 services with proper relationships
- ✅ Color-coded clusters by type
- ✅ Edge labels for connection types
- ✅ AWS best practices highlighted
- ✅ Comprehensive validation report

### Example 3: E-Commerce Platform

**Input:**
```
Production e-commerce with CloudFront CDN, ALB load balancer,
Lambda microservices, RDS PostgreSQL database, and S3 for images
```

**Generated Diagram:**
```python
import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.network import CloudFront, ALB
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3
from diagrams.aws.general import Users

COLOR_PROD = "#E74C3C"
COLOR_COMPUTE = "#3498DB"
COLOR_DATABASE = "#27AE60"
COLOR_STORAGE = "#F39C12"

with Diagram("E-Commerce Platform", show=False, filename="ecommerce", direction="TB"):
    users = Users("End Users")
    cdn = CloudFront("CloudFront CDN")

    with Cluster("Load Balancing"):
        lb = ALB("Application Load Balancer")

    with Cluster("Compute"):
        lambda_func = Lambda("Microservices")

    with Cluster("Database"):
        db = RDS("PostgreSQL")

    with Cluster("Storage"):
        storage = S3("Product Images")

    users >> Edge(label="HTTPS") >> cdn
    cdn >> lb >> lambda_func
    lambda_func >> Edge(label="Reads/Writes") >> db
    lambda_func >> Edge(label="Stores") >> storage
```

## 🏗️ Architecture

### Project Structure

```
cloudforge/
├── src/
│   ├── presentation/
│   │   ├── api.py                              # FastAPI with /refine & /generate
│   │   ├── api_models.py                       # RefineRequest, GenerateRequest, etc.
│   │   └── server.py                           # MCP server
│   │
│   ├── application/
│   │   └── services.py                         # Business logic services
│   │
│   ├── infrastructure/
│   │   ├── config.py                           # Configuration management
│   │   ├── langchain_chains.py                 # DescriptionRefinerChain, BlueprintArchitectChain, DiagramCoderChain
│   │   ├── langgraph_pipeline.py               # LangGraph 5-node pipeline
│   │   ├── validator.py                        # AST validation + security
│   │   ├── generator.py                        # Dynamic imports + diagram generation
│   │   ├── storage.py                          # Persistent storage layer
│   │   ├── aws_mcp_client.py                   # AWS MCP integration
│   │   └── natural_language.py                 # NLP utilities
│   │
│   └── domain/
│       └── models.py                           # Core domain models

├── ui/
│   ├── app.py                                  # Streamlit 2-step UI
│   ├── api_client.py                           # CloudForgeAPIClient
│   └── utils.py                                # UI utilities

├── examples/
│   ├── basic_serverless.py                     # Simple example
│   ├── multi_tier_saas.py                      # Complex example
│   └── multi_region_app.py                     # Advanced example

├── docker-compose.yml                          # Multi-container orchestration
├── Dockerfile.api                              # API container
├── Dockerfile.ui                               # UI container
├── Makefile                                    # Convenience commands
├── .env.example                                # Environment variables
├── pyproject.toml                              # Project metadata
├── uv.lock                                     # Dependency lock file
└── README.md                                   # This file
```

### Key Components

- **API (`src/presentation/api.py`)**:
  - `POST /v1/diagrams/refine` - Refine description
  - `POST /v1/diagrams/generate` - Generate diagram

- **LangChain Chains**:
  - `DescriptionRefinerChain` - Enhances descriptions (exported to API)
  - `BlueprintArchitectChain` - Generates blueprint from description
  - `DiagramCoderChain` - Generates diagram code from blueprint

- **LangGraph Pipeline**: 5-node orchestration
  - blueprint → enrich_mcp → coder → validator → generator

- **AWS MCP Integration**: Consults AWS Documentation MCP
  - Auto-enriches with best practices
  - Service-specific recommendations

- **Generator**: Dynamic wildcard imports + execution
  - All 1000+ diagrams symbols available
  - Eliminates import errors

- **Storage**: Persists diagrams with metadata

## 🧪 Testing

### Run All Tests

```bash
# Execute all tests
pytest -xvs tests/

# Run with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test file
pytest -xvs tests/test_validator.py
```

## 🔧 Troubleshooting

### "GraphViz not found"

```bash
# macOS
brew install graphviz

# Linux (Ubuntu/Debian)
sudo apt-get install graphviz

# Windows (Chocolatey)
choco install graphviz
```

### "Module not found: diagrams"

```bash
uv sync
```

### API/UI Connection Issues

```bash
# Verify API is running
curl http://localhost:8000/health

# Check API port
lsof -i :8000

# Verify UI can reach API
# In .env: CLOUDFORGE_API_URL=http://localhost:8000
```

## 📋 Supported AWS Services

### Compute
- Lambda, EC2, ECS, EKS, Batch, Lightsail

### Database
- RDS, DynamoDB (DynamodbTable), ElastiCache, Redshift, Aurora, DocumentDB, Neptune, DAX

### Storage
- S3, EBS, EFS, Glacier, StorageGateway

### Network
- API Gateway, ALB, NLB, Route53, NATGateway, CloudFront, VPC Endpoint

### Integration
- SQS, SNS, Kinesis, EventBridge, MQ

### Monitoring
- CloudWatch, CloudWatch Logs

### Security
- IAM, Secrets Manager, ACM, WAF, GuardDuty

### Plus K8S, On-Prem, Generic, and SaaS services!

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

## 📝 Recent Updates (v0.2.0)

**✨ Features:**
- ✅ AWS MCP Integration - Automatic best practices enrichment
- ✅ Description Refinement - Smart enhancement of vague descriptions
- ✅ Dynamic Imports - All diagrams symbols available automatically
- ✅ 2-Step Workflow - User reviews refined description before generation
- ✅ /v1/diagrams/refine endpoint - Standalone refinement API
- ✅ Improved Streamlit UI - Clear workflow with status indicators

**🔧 Technical:**
- ✅ LangGraph pipeline refined (5 nodes, no duplicate refinement)
- ✅ AWS Documentation MCP integration for best practices
- ✅ Dynamic wildcard imports in DiagramGenerator
- ✅ Better system prompts for code generation
- ✅ Cleaner separation of concerns (UI refinement vs Graph generation)

**🎯 Key Improvements:**
- Prevents hallucination through user approval
- AWS best practices automatically applied
- Easier diagram generation from brief descriptions
- 100% confidence in generated content
- Better code quality with fewer retries

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [Diagrams](https://diagrams.mingrammer.com/)
- Powered by [Model Context Protocol](https://modelcontextprotocol.io)
- AWS MCP for best practices integration
- [LangChain](https://python.langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/)
- [FastAPI](https://fastapi.tiangolo.com/) and [Streamlit](https://streamlit.io)
- Package management by [UV](https://astral.sh/uv/)

---

**CloudForge** - Forge your cloud architecture with AI ⚡

*Generate professional AWS diagrams in 2 simple steps with AI-powered refinement and AWS best practices*
