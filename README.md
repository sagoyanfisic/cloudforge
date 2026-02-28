# CloudForge

**AI-Powered AWS Architecture Diagrams from Natural Language**

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org)
[![LangChain](https://img.shields.io/badge/LangChain-v0.1.0-orange)](https://python.langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-blueviolet)](https://langchain-ai.github.io/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-009688)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20UI-red)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Yes-brightgreen)](https://www.docker.com)
[![AWS Well-Architected](https://img.shields.io/badge/AWS-Well--Architected-FF9900)](https://aws.amazon.com/architecture/well-architected/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

CloudForge generates **production-grade AWS architecture diagrams** from plain English descriptions. Using a 7-stage NLP pipeline, it transforms a simple description into a comprehensive, multi-service architecture diagram with AWS Well-Architected Framework validation.

Generate **20-27+ service architectures** with intelligent clustering, automatic service naming corrections, and architectural best practices enforcement.

---

## ✨ Core Features

### 🎯 Smart Architecture Generation
- **Description refinement** — AI expands brief descriptions into comprehensive, production-grade architectures (20-27+ services)
- **AWS Well-Architected evaluation** — Automatic scoring across 5 pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization
- **Pattern detection** — Identifies architecture patterns (RAG, Serverless API, Data Pipeline, Streaming Analytics, ML Platform, Event-Driven, CDN, IoT, Kubernetes, Generative AI, High Availability, Data Warehouse, Security & Compliance)

### 🔧 Intelligent Code Generation
- **Dynamic service mapping** — 30+ automatic service name corrections (OpenSearch → AmazonOpensearchService, EventBridge → Eventbridge, etc.)
- **Smart fallback system** — Unmapped services automatically use generic Rack icon with service label (prevents NameErrors for 20+ additional services)
- **LangGraph pipeline** — 7-node state machine: pattern detection → well-architected assessment → blueprint → code → validation → retry logic → rendering

### 📊 Production-Grade Visualization
- **VPC clustering** — VPC container wraps services logically; removes granular VPC Endpoints for high-level diagrams
- **Sparse connections** — 15-30 meaningful connections for 20+ services (not every-to-every)
- **Logical grouping** — Clusters: VPC, Public/Private Subnets, Monitoring, Security & Identity, Integration & Events, Storage & Search
- **Full diagram validation** — AST parse, security scan, AWS component whitelist before execution

### 🛠️ Complete Pipeline
- **Multi-agent NLP** — Architect + Critic + Reviewer agents validate architecture patterns
- **REST API + Web UI** — FastAPI backend with Streamlit frontend for 2-step workflow
- **Multiple output formats** — PNG, PDF, SVG rendering
- **Error recovery** — Smart retry logic regenerates code if diagram execution fails (up to 9 total attempts)

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

## 🏗️ Architecture & Pipeline

### User Workflow

```
1. Enter description      →  "E-commerce platform with multi-tier services"
2. Click Refine           →  AI expands to 20-27+ services with best practices
3. Review well-architected assessment  →  See pillar scores and gaps
4. Review & approve       →  Edit refined description if needed
5. Generate               →  Diagram rendered with 30+ auto-corrections applied
```

### 7-Stage NLP Pipeline (LangGraph)

```
User Input
    │
    ▼
[1] AWS Pattern Detection  (AwsPatternSkill — Architect + Critic + Reviewer agents)
                           Identifies architecture patterns, validates design
    │
    ▼
[2] Well-Architected Evaluation  (WellArchitectedSkill)
                           Scores against 5 pillars: Operational Excellence, Security,
                           Reliability, Performance Efficiency, Cost Optimization
    │
    ▼
[3] Description Refinement  (DescriptionRefinerChain — Gemini 2.5-Flash)
                           Expands to 20+ services, adds data flows, layers, best practices
    │
    ▼
[4] Blueprint Generation  (BlueprintArchitectChain — Gemini 2.5-Flash)
                          Extracts services, relationships → structured JSON with clustering
    │
    ▼
[5] Code Generation  (DiagramCoderChain — Gemini 2.5-Flash)
                     JSON blueprint → Python diagrams code
    │
    ▼
[6] Validation & Auto-Fix  (DiagramValidator + 30+ regex auto-fixes)
                           AST parse · security scan · service name corrections
                           • 30+ explicit mappings (OpenSearch, EventBridge, etc.)
                           • Smart fallback: unmapped services → Rack("ServiceName")
    │
    ├─ [If code fails] ─→ Loop back to [5] (regenerate code, up to 3 times)
    │
    ▼
[7] Rendering  (DiagramGenerator — Wildcard imports + exec)
               Executes code with all diagrams symbols pre-imported
               PNG / PDF / SVG output
```

### Key Design Decisions

#### 📐 High-Level Architecture Focus
- **VPC as container** — Services shown as VPC members (via clustering), not granular VPC Endpoints
- **Sparse connections** — 15-30 meaningful edges for 20+ services (avoids visual chaos)
- **Logical clusters** — VPC, Public/Private Subnets, Monitoring, Security, Integration, Storage (visual hierarchy)

#### 🤖 Smart Service Handling
- **Explicit mappings** — 30 common service names (OpenSearch, EventBridge, DynamoDB, etc.)
- **Intelligent fallback** — Unmapped services (GuardDuty, Forecast, Bedrock, etc.) use `Rack("ServiceName")` generic icon
- **No code failures** — Prevents NameErrors; diagrams always render even with unknown services

#### ✅ Production-Grade Best Practices
- **Well-Architected Framework** — Integrated pillar evaluation before code generation
- **Architecture patterns** — 13 pattern templates (RAG, Serverless, Data Pipeline, Streaming, ML, Event-Driven, CDN, IoT, Kubernetes, Generative AI, HA/DR, Data Warehouse, Security)
- **Multi-agent validation** — Architect + Critic + Reviewer ensure design coherence

---

## 🎯 Real-World Examples

### Example 1: E-Commerce Production Platform (26 Services)

**Input Description:**
```
Enterprise e-commerce platform with multi-region support,
fraud detection, real-time inventory, and order processing.
```

**Generated Architecture:**
```
✅ Route53 (DNS failover)
✅ CloudFront (CDN global distribution)
✅ WAF + ALB (entry point security)
✅ ECS (4 containerized microservices)
✅ RDS (multi-AZ database)
✅ DynamoDB (sessions, cart state)
✅ ElastiCache (Redis for hot data)
✅ OpenSearch (product catalog search)
✅ S3 (static assets, inventory data)
✅ SQS + SNS (async order processing)
✅ EventBridge (event orchestration)
✅ Cognito (user authentication)
✅ Secrets Manager (credentials, API keys)
✅ KMS (encryption keys)
✅ GuardDuty (threat detection)
✅ CloudWatch + X-Ray (observability)
✅ CloudWatch Logs (centralized logging)
✅ NAT Gateway (outbound VPC traffic)
✅ IAM (least privilege access)
+ 7 more services across monitoring, security, integration layers
```

**Metrics:**
- **Nodes:** 26 services
- **Clusters:** 8 (VPC, Public/Private Subnets, Monitoring, Security, Integration, Storage, etc.)
- **Relationships:** 60+ (sparse but meaningful)
- **Auto-Fixes Applied:** DynamoDB → DynamodbTable, EventBridge → Eventbridge, OpenSearch → AmazonOpensearchService, GuardDuty → Rack("GuardDuty")
- **Result:** ✅ Production-grade diagram, 477KB PNG, 60+ logical connections

---

### Example 2: Video Streaming Platform (27 Services)

**Input Description:**
```
Global video streaming service with transcoding, caching,
adaptive bitrate delivery, and real-time analytics.
```

**Generated Architecture:**
```
✅ Route53 (geo-routing for global users)
✅ CloudFront (content delivery network)
✅ API Gateway + ALB (entry points)
✅ WAF (API protection)
✅ Lambda (compute for encoding, metadata)
✅ S3 (video storage, manifests)
✅ RDS (metadata, user accounts)
✅ DynamoDB (sessions, playback state)
✅ ElastiCache (cache layer)
✅ OpenSearch (video search indexing)
✅ SQS (transcode job queue)
✅ SNS (notification fan-out)
✅ EventBridge (pipeline orchestration)
✅ MediaConvert (video transcoding) → Auto-fixed to Rack("MediaConvert")
✅ SageMaker (ML for recommendations) → Auto-fixed to Rack("SageMaker")
✅ Cognito (user auth)
✅ Secrets Manager (API keys, DB passwords)
✅ KMS (data encryption)
✅ CloudWatch + X-Ray (monitoring)
+ 8 more services (IAM, Backup, monitoring, security)
```

**Metrics:**
- **Nodes:** 27 services
- **Clusters:** 7 (logical grouping for readability)
- **Relationships:** 30 (sparse, main flow only)
- **Auto-Fixes Applied:** 8+ services corrected
- **Result:** ✅ Clean, readable diagram with 30 connections

---

### Example 3: IoT Monitoring Platform (26 Services)

**Input Description:**
```
Real-time IoT device monitoring with anomaly detection,
remote control, and multi-tenant analytics.
```

**Generated Architecture:**
- **IoT Services:** IoT Core, IoT Greengrass, IoT Analytics, IoT Events, IoT SiteWise
- **Processing:** Lambda (stream processing)
- **Storage:** S3 (raw data), DynamoDB (device state), RDS (analytics)
- **Analytics:** Kinesis (data streams), OpenSearch (log analysis)
- **Visualization:** QuickSight (dashboards)
- **Security:** Cognito, Secrets Manager, GuardDuty, KMS
- **Monitoring:** CloudWatch, X-Ray

**Result:** ✅ All IoT services handled (some auto-fixed to Rack, fully functional)

---

## 📊 Performance & Capabilities

| Metric | Value | Notes |
|--------|-------|-------|
| **Max Services** | 27+ | Successfully tested with 27-node architectures |
| **Auto-Fix Patterns** | 30+ | Explicit mappings + smart fallback |
| **Clusters Supported** | 8+ | VPC, subnets, functional groupings |
| **Connection Density** | 15-30 | Sparse (readable), not every-to-every |
| **Code Size** | 7-9KB | Complete code for 20+ services |
| **Render Time** | 2-5s | PNG generation with GraphViz |
| **Retry Attempts** | 9 max | 3 execution attempts × 3 code regenerations |
| **Pattern Templates** | 13 | RAG, Serverless, Data, Streaming, ML, Event-Driven, CDN, IoT, K8s, GenAI, HA, DW, Security |

---

## 🔍 Well-Architected Framework Integration

Every architecture is evaluated against **5 AWS pillars** before rendering:

### 1. **Operational Excellence**
- Recommendations: CloudWatch, X-Ray, CloudWatch Logs, EventBridge, Systems Manager, Config
- Checks: monitoring, logging, automation, runbooks

### 2. **Security**
- Recommendations: IAM, Cognito, Secrets Manager, KMS, WAF, GuardDuty, Inspector, Macie, VPC
- Checks: access control, encryption, threat detection, compliance

### 3. **Reliability**
- Recommendations: Multi-AZ, Auto Scaling, RDS Multi-AZ, Route 53, Backup, SQS, SNS, DynamoDB Global Tables
- Checks: redundancy, failover, backups, auto-recovery

### 4. **Performance Efficiency**
- Recommendations: CloudFront, ElastiCache, RDS Read Replicas, DynamoDB On-Demand, Lambda, Global Accelerator
- Checks: caching, CDN, database optimization, right-sizing

### 5. **Cost Optimization**
- Recommendations: Cost Explorer, Budgets, Compute Optimizer, Savings Plans, Spot Instances, S3 Lifecycle
- Checks: right-sizing, reserved capacity, lifecycle policies, tagging

**Result:** Architecture gets scored 0-100 per pillar + overall score + specific gap recommendations.

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/diagrams/refine` | Refine description + get Well-Architected assessment |
| `POST` | `/v1/diagrams/generate` | Generate complete diagram with auto-fixes |
| `GET` | `/v1/diagrams/history` | List recent diagrams with metadata |
| `GET` | `/v1/diagrams/{id}` | Get diagram details by ID |
| `GET` | `/images/{filename}` | Serve PNG / PDF / SVG |
| `GET` | `/health` | Health check |

**Interactive docs:** `http://localhost:8000/docs`

### Refine a Description

Expands brief input into production-grade architecture (20-27+ services) with pattern detection and Well-Architected assessment:

```bash
curl -X POST http://localhost:8000/v1/diagrams/refine \
  -H "Content-Type: application/json" \
  -d '{
    "description": "E-commerce platform with real-time inventory and fraud detection"
  }'
```

**Response:**
```json
{
  "success": true,
  "original": "E-commerce platform with real-time inventory and fraud detection",
  "refined": "Enterprise e-commerce platform featuring...\n- API Gateway + ALB entry points\n- ECS microservices\n- RDS multi-AZ database...",
  "pattern": "serverless_rest_api",
  "well_architected": {
    "pillars": [
      {
        "pillar": "Operational Excellence",
        "score": 78,
        "strengths": ["CloudWatch monitoring", "X-Ray tracing"],
        "gaps": ["Missing CloudWatch Logs aggregation", "No EventBridge automation"],
        "recommendations": ["Add CloudWatch Logs", "Implement EventBridge for ops events"]
      },
      ...
    ],
    "overall_score": 82,
    "summary": "Strong security posture with multi-AZ database..."
  },
  "message": "Description refined with 24 services, pattern detected, and architecture assessment complete"
}
```

### Generate a Diagram

Generates diagram from description with automatic service name corrections (30+ mappings):

```bash
curl -X POST http://localhost:8000/v1/diagrams/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "E-commerce platform with Route53, CloudFront, API Gateway, Lambda, RDS, DynamoDB, ElastiCache, OpenSearch, SQS, SNS, EventBridge, Cognito, Secrets Manager, KMS, GuardDuty, CloudWatch, X-Ray, and more",
    "name": "ecommerce_platform"
  }'
```

**Response:**
```json
{
  "success": true,
  "diagram_id": "ecommerce_platform_2024_02_27_143025",
  "name": "ecommerce_platform",
  "file_path": "/path/to/ecommerce_platform.png",
  "format": "png",
  "size_bytes": 487234,
  "services_count": 26,
  "clusters_count": 8,
  "relationships_count": 60,
  "auto_fixes_applied": [
    "OpenSearch() → AmazonOpensearchService()",
    "EventBridge() → Eventbridge()",
    "DynamoDB() → DynamodbTable()",
    "GuardDuty() → Rack('GuardDuty')",
    "...and 10+ more"
  ],
  "validation_report": {
    "ast_valid": true,
    "security_checks_passed": 15,
    "unauthorized_symbols": [],
    "execution_time_ms": 2847
  },
  "message": "Diagram generated successfully with 26 AWS services across 8 clusters"
}
```

### List Recent Diagrams

```bash
curl http://localhost:8000/v1/diagrams/history?limit=10
```

### Get Specific Diagram

```bash
curl http://localhost:8000/v1/diagrams/ecommerce_platform_2024_02_27_143025
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_key
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | *(required)* | Google Gemini 2.5-Flash API key |
| `AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH` | `~/.aws_diagrams` | Where diagrams and metadata are saved |
| `AWS_DIAGRAM_OUTPUT_FORMATS` | `png,pdf,svg` | Output formats (comma-separated) |
| `AWS_DIAGRAM_LOG_LEVEL` | `INFO` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) |
| `CLOUDFORGE_DISABLE_AWS_MCP` | `1` | Set to `0` to enable AWS Documentation MCP enrichment |
| `CLOUDFORGE_API_URL` | `http://localhost:8000` | API base URL (used by Streamlit UI) |
| `STREAMLIT_SERVER_PORT` | `8501` | Streamlit web UI port |
| `FASTAPI_PORT` | `8000` | FastAPI backend port |

### LangChain Configuration

Pipeline uses **Gemini 2.5-Flash** with optimized parameters:
- `temperature: 0.3` — Deterministic outputs, reproducible diagrams
- `max_output_tokens: 10000` — Supports 20-27+ service architectures
- `retry_policy: stop_after_attempt=2` — Smart error recovery

### Diagram Generation Settings

- **Max services:** 27+ (tested with E-commerce and Video Streaming platforms)
- **Target connections:** 15-30 (sparse, meaningful relationships)
- **Clusters:** 8+ (VPC, subnets, logical groupings)
- **Auto-fixes:** 30+ service name corrections
- **Render time:** 2-5 seconds (GraphViz)

---

## 📁 Project Structure

```
mcp-aws/
├── src/
│   ├── presentation/
│   │   ├── api.py                    # FastAPI app — /refine, /generate, /history
│   │   └── api_models.py             # Pydantic request/response models
│   ├── application/
│   │   └── services.py               # Use-case services + repository pattern
│   ├── infrastructure/
│   │   ├── nlp/                      # 🆕 NLP subpackage (refactored from monolithic chains)
│   │   │   ├── chains.py             # DescriptionRefiner, BlueprintArchitect, DiagramCoder
│   │   │   ├── skill.py              # AwsPatternSkill (Architect + Critic + Reviewer agents)
│   │   │   ├── outputs.py            # Pydantic models for LLM outputs
│   │   │   └── well_architected_skill.py  # 🆕 Well-Architected Framework evaluation
│   │   ├── skills/                   # 🆕 Prompt templates + skill definitions
│   │   │   ├── chains/
│   │   │   │   ├── refiner.md        # Description refinement (expand to 20+ services)
│   │   │   │   ├── pattern_skill.md  # Pattern detection instructions
│   │   │   │   ├── blueprint.md      # JSON blueprint generation rules
│   │   │   │   └── coder.md          # Python diagrams code generation (30+ service mappings)
│   │   │   ├── agents/
│   │   │   │   ├── architect.md      # Architect agent persona
│   │   │   │   ├── critic.md         # Critic agent (validates design)
│   │   │   │   └── reviewer.md       # Reviewer agent (final synthesis)
│   │   │   ├── aws_patterns.md       # 13 architecture patterns with Mermaid diagrams
│   │   │   └── well_architected.md   # 🆕 5-pillar framework guidelines (40+ service recommendations)
│   │   ├── langgraph_pipeline.py     # 7-node LangGraph state machine (with retry logic)
│   │   ├── generator.py              # Wildcard imports + diagram execution
│   │   ├── validator.py              # AST validation + security scan + 30+ auto-fixes
│   │   ├── storage.py                # File-based storage with JSON index
│   │   ├── aws_mcp_client.py         # AWS Documentation MCP client (optional)
│   │   ├── mcp_client.py             # MCP direct client
│   │   ├── server.py                 # MCP server tools
│   │   └── config.py                 # pydantic-settings configuration
│   └── domain/
│       └── models.py                 # Domain models + exceptions
├── ui/
│   ├── app.py                        # Streamlit 2-step UI with refinement + approval
│   └── api_client.py                 # HTTP client for the API
├── docker/
│   ├── Dockerfile.api
│   └── Dockerfile.ui
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── .env.example
└── .claude/
    └── projects/
        └── mcp-aws/
            └── memory/               # Session memory (architecture patterns, common errors)
                ├── MEMORY.md         # Latest session notes
                └── [topic-specific docs]
```

### Key NLP Modules

| Module | Purpose |
|--------|---------|
| `nlp/chains.py` | 3-chain pipeline: DescriptionRefiner → BlueprintArchitect → DiagramCoder |
| `nlp/skill.py` | Multi-agent pattern detection (Architect + Critic + Reviewer) |
| `nlp/well_architected_skill.py` | 5-pillar evaluation (Gemini LLM) + gap recommendations |
| `nlp/outputs.py` | Pydantic models for LLM outputs (AwsPatternSkillOutput, BlueprintAnalysis, etc.) |
| `langgraph_pipeline.py` | 7-node orchestration with conditional edges + retry logic |

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

## 🔧 Advanced Topics

### Adding New Architecture Patterns

1. **Define pattern in `aws_patterns.md`:**
   ```markdown
   ## YourPattern

   **Flow:** User → Lambda → DynamoDB
   **Services:** Lambda, DynamoDB, API Gateway, CloudWatch, IAM
   **Checklist:**
   - [ ] Include monitoring (CloudWatch, X-Ray)
   - [ ] Add security layer (IAM, KMS)
   ```

2. **Pattern is auto-detected** by AwsPatternSkill agents

3. **Refinement automatically applies** best practices from pattern

### Extending Well-Architected Evaluation

1. **Edit `well_architected.md`** to add/update pillar guidance
2. **Modify `well_architected_skill.py`** if custom scoring logic needed
3. **Assessment automatically** runs before code generation

### Understanding Auto-Fixes

The system applies **30+ automatic service name corrections** in two layers:

**Layer 1: Explicit Mappings** (in `chains.py`):
```python
r'OpenSearch\(': 'AmazonOpensearchService(',
r'EventBridge\(': 'Eventbridge(',
r'DynamoDB\(': 'DynamodbTable(',
```

**Layer 2: Smart Fallback** (catch-all regex):
```python
# Any undefined CamelCase class → Rack("ServiceName")
r'\b([A-Z][a-zA-Z0-9]*)\('
  → 'Rack(' if not in known_classes
```

**Result:** Even unmapped services (GuardDuty, Forecast, Bedrock, IoT services) render successfully.

### Custom Service Mappings

To add a new explicit mapping:

1. **Edit `src/infrastructure/nlp/chains.py`** line 275-330 (in `_fix_invalid_service_names`):
   ```python
   r'CustomService\(': 'CorrectService(',
   ```

2. **Update `coder.md`** service mapping table to document the fix

3. **Test with:** Diagram using CustomService in description

### Debugging LLM Outputs

1. **Check Docker logs:**
   ```bash
   make logs  # Tails API logs
   ```

2. **Enable DEBUG logging:**
   ```bash
   AWS_DIAGRAM_LOG_LEVEL=DEBUG make up
   ```

3. **Inspect generated blueprint** (API response includes full JSON)

4. **Inspect generated code** (logs show Python code before execution)

---

## 🚀 Troubleshooting Guide

### GraphViz not found
```bash
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt install graphviz

# Verify installation
dot -V
```

### `diagrams` module not found
```bash
uv sync
# Or in Docker:
make rebuild
```

### API unreachable from UI
```bash
# Check if API is running
curl http://localhost:8000/health

# Verify CLOUDFORGE_API_URL in .env
echo $CLOUDFORGE_API_URL
# Should match: http://localhost:8000
```

### Diagram generation times out (>10s)
- **Check logs:** `make logs` — look for LLM API delays
- **Verify GraphViz:** `dot -V` should complete instantly
- **Increase token limit** in `chains.py` if generating 25+ services

### "NameError: name 'SomeService' is not defined"
- **Expected:** Smart fallback uses `Rack("SomeService")`
- **If fails:** Service exists in `diagrams` library but wasn't caught
  - Add explicit mapping to `chains.py` line 275-330
  - File an issue on GitHub with service name

### "AST validation failed" or "Unterminated string"
- **Likely cause:** Unescaped quotes in service labels
- **Check:** Generated code in API response (before execution)
- **Fix:** Edit description to use simpler names without special chars

### Well-Architected score is 0
- **Check:** Refiner API response includes `well_architected` field
- **Debug:** Manually call `/v1/diagrams/refine` endpoint
- **Verify:** GOOGLE_API_KEY is valid and has quota

### Docker container exits immediately
```bash
# Check logs
docker logs mcp-aws-api-1

# Rebuild and restart
make rebuild
make up
```

### Pattern not detected
- **Check:** Description matches pattern keywords
- **List:** `aws_patterns.md` line 5-12 shows detection triggers
- **Debug:** Call `/v1/diagrams/refine` to see detected pattern in response

---

## 📚 Architecture Patterns Supported

CloudForge recognizes and optimizes for **13 AWS architecture patterns**:

1. **RAG / Semantic Search** — LLM + vector DB + retrieval
2. **Serverless REST API** — API Gateway + Lambda + DynamoDB
3. **Data Pipeline / ETL** — S3 + Glue + Redshift/DW
4. **Real-time Streaming Analytics** — Kinesis + Spark + BI
5. **ML Platform / MLOps** — SageMaker + S3 + Lambda
6. **Event-Driven Architecture** — EventBridge + Lambda + SNS
7. **Static Website / CDN** — S3 + CloudFront + Route53
8. **IoT Platform** — IoT Core + Greengrass + Analytics
9. **Container Platform / Kubernetes** — ECS / EKS + ALB + RDS
10. **Generative AI / LLM Application** — Bedrock + RAG + Lambda
11. **High Availability / Disaster Recovery** — Multi-AZ + Failover + Backup
12. **Analytics / Data Warehouse** — Redshift + Glue + QuickSight
13. **Security & Compliance** — GuardDuty + Security Hub + KMS + Audit

Each pattern includes recommended services, multi-agent validation, and Well-Architected checks.

---

## 🎓 Best Practices for Descriptions

### ✅ Good Description
```
"Enterprise e-commerce platform with:
- Multi-region global distribution
- Fraud detection and real-time inventory
- Microservice-based order processing
- Multi-tier security with SSO
- Real-time analytics and dashboards"
```
**Result:** 25-27 services, 8+ clusters, complete architecture

### ❌ Poor Description
```
"Shopping website"
```
**Result:** Only 5-8 services, minimal architecture

**Tip:** Use keywords that trigger Well-Architected pillars:
- **Operational Excellence:** monitoring, logging, automation, runbooks
- **Security:** encryption, authentication, multi-factor, least privilege
- **Reliability:** failover, backups, multi-AZ, auto-scaling
- **Performance:** caching, CDN, read replicas, global distribution
- **Cost:** right-sizing, lifecycle policies, spot instances, reserved capacity

---

## 📖 Documentation & Skills

| File | Purpose | Location |
|------|---------|----------|
| `aws_patterns.md` | 13 architecture patterns with Mermaid diagrams | `src/infrastructure/skills/` |
| `well_architected.md` | 5-pillar guidelines + 40+ service recommendations | `src/infrastructure/skills/` |
| `refiner.md` | Prompt for expanding 20+ service architectures | `src/infrastructure/skills/chains/` |
| `blueprint.md` | JSON blueprint generation rules + clustering | `src/infrastructure/skills/chains/` |
| `coder.md` | 30+ service name mappings + Python code rules | `src/infrastructure/skills/chains/` |
| `architect.md`, `critic.md`, `reviewer.md` | Multi-agent prompts | `src/infrastructure/skills/agents/` |

All prompts are **externally editable** (no hardcoding in Python). Changes apply immediately.

---

## 🤝 Contributing

1. **Fix a service mapping:** Edit `chains.py` + `coder.md`
2. **Add a pattern:** Edit `aws_patterns.md` + `refiner.md`
3. **Improve Well-Architected:** Edit `well_architected.md`
4. **Report a bug:** Include description, generated code, and error message

---

## 📄 License

MIT — see [LICENSE](LICENSE).
