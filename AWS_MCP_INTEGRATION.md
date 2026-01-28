# AWS MCP Integration for CloudForge

This document describes how CloudForge integrates with AWS Labs MCP servers to enhance architecture diagram generation with real-time AWS best practices.

## Overview

CloudForge now supports optional integration with two AWS Labs MCP servers:

1. **awslabs.aws-documentation-mcp-server** - Provides real-time AWS documentation and best practices
2. **awslabs.aws-diagram-mcp-server** - Alternative diagram generation with AWS best practices (experimental)

## Architecture

```
┌─────────────┐
│  CloudForge │
│    User     │
└──────┬──────┘
       │
       ├─────────────────────────────────────────────┐
       │                                             │
       ▼                                             ▼
  ┌─────────────┐  (Primary)              ┌─────────────────────┐  (Optional)
  │   Gemini    │                         │  AWS MCP Clients    │
  │  Blueprint  │◄─────AWS Best Practices─│  (Documentation +   │
  │  Architect  │  (via Documentation)    │   Diagram Servers)  │
  └──────┬──────┘                         └─────────────────────┘
         │
         ├─► Parse Blueprint
         │
         ▼
  ┌─────────────────┐
  │  Diagram Coder  │
  │  (Gemini + Fix) │
  └────────┬────────┘
           │
           ▼
    ┌─────────────┐
    │ Diagram Gen │
    │  (Graphviz) │
    └─────────────┘
```

## Installation

### Prerequisites

```bash
# Install uv (required for uvx)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip
pip install uv
```

### Setup

1. **Configuration file is included**: `mcp.json` contains server definitions

2. **Install Python dependencies** (if running with AWS MCP):
   ```bash
   pip install awslabs.aws-diagram-mcp-server
   pip install awslabs.aws-documentation-mcp-server
   ```

3. **Optional environment variable**: Set if running outside Docker
   ```bash
   export CLOUDFORGE_AWS_MCP_ENABLED=1
   ```

## Usage

### Automatic (Default)

CloudForge automatically attempts to use AWS Documentation server if available:

1. When analyzing architecture description, detects AWS services mentioned
2. Calls AWS Documentation MCP to get best practices for detected services
3. Enriches the Gemini prompt with real-time AWS documentation
4. Generates improved blueprint with AWS best practices baked in

**Example flow:**
```
User: "I need a serverless API with Lambda, DynamoDB, and API Gateway"
       │
       ▼
CloudForge detects: Lambda, DynamoDB, API Gateway
       │
       ▼
Calls AWS Documentation for best practices on:
  - Lambda + serverless patterns
  - DynamoDB + serverless patterns
  - API Gateway + serverless patterns
       │
       ▼
Enriches Gemini prompt with AWS recommendations
       │
       ▼
Generates blueprint with AWS best practices incorporated
```

### Manual (Code)

If you want to use AWS MCP clients directly:

```python
from src.infrastructure.aws_mcp_client import (
    get_aws_documentation_client,
    get_aws_diagram_client
)

# Get AWS best practices for a service
doc_client = get_aws_documentation_client()
if doc_client.connect():
    practices = doc_client.get_best_practices("Lambda", "serverless")
    print(practices)
    doc_client.close()

# Alternative: Use AWS Diagram server
diagram_client = get_aws_diagram_client()
if diagram_client.connect():
    result = diagram_client.generate_diagram(
        "REST API with Lambda and DynamoDB",
        "my_api"
    )
    print(result)
    diagram_client.close()
```

## Configuration

### MCP Servers Config (`mcp.json`)

The `mcp.json` file defines available MCP servers:

```json
{
  "mcpServers": {
    "awslabs.aws-diagram-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-diagram-mcp-server"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false
    },
    "awslabs.aws-documentation-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false
    }
  }
}
```

To disable AWS MCP integration:
```json
"disabled": true
```

### Environment Variables

- `CLOUDFORGE_AWS_MCP_ENABLED=1` - Force enable AWS MCP (default: auto-detect)
- `CLOUDFORGE_AWS_MCP_ENABLED=0` - Force disable AWS MCP
- `FASTMCP_LOG_LEVEL=DEBUG` - Set MCP server logging level

## Features

### 1. AWS Documentation Enrichment

When available, the AWS Documentation MCP server:

- **Extracts Services** from user description
- **Searches AWS Docs** for each detected service
- **Returns Best Practices** specific to the detected pattern (serverless, microservices, etc.)
- **Enriches Gemini Prompt** with real-time AWS recommendations
- **Improves Blueprint Quality** with AWS best practices built-in

**Detected Services** (when mentioned in description):
- `lambda` → Lambda best practices
- `dynamodb` → DynamoDB best practices
- `rds` → RDS best practices
- `api gateway` → API Gateway best practices
- `s3`, `sqs`, `sns`, `kinesis` → Individual service practices
- `cloudwatch` → Monitoring best practices

### 2. AWS Diagram Server (Experimental)

Alternative diagram generation engine:

- **Use Case 1**: Validation - Compare CloudForge diagram against AWS implementation
- **Use Case 2**: Fallback - If Gemini generation fails, try AWS server
- **Use Case 3**: Benchmarking - Compare output quality
- **Use Case 4**: AWS Best Practices** - AWS server may generate diagrams more aligned with AWS patterns

To use AWS Diagram server instead of CloudForge:
```python
from src.infrastructure.aws_mcp_client import get_aws_diagram_client

aws_diagram_client = get_aws_diagram_client()
if aws_diagram_client.connect():
    result = aws_diagram_client.generate_diagram(description, name)
    # result includes generated code, image path, etc.
```

## Logging

CloudForge logs AWS MCP integration status:

```bash
# When AWS Documentation enrichment works
INFO:src.infrastructure.natural_language:🔍 Enriching with AWS best practices...
INFO:src.infrastructure.natural_language:✅ Enriched with best practices for: lambda, dynamodb, api_gateway

# When AWS servers are unavailable (gracefully degraded)
WARNING:src.infrastructure.natural_language:⚠️ Could not connect to AWS Documentation server
# (CloudForge continues with standard Gemini generation)

# When MCP clients close
INFO:src.infrastructure.aws_mcp_client:✅ AWS Documentation MCP client closed
```

## Error Handling

CloudForge gracefully handles AWS MCP unavailability:

1. **MCP Servers Not Installed** → Logs warning, continues with standard pipeline
2. **MCP Servers Unavailable** → Attempts connection, times out, continues
3. **MCP Servers Crash** → Catches error, logs it, continues with Gemini only
4. **Network Issues** → Connection timeout, graceful fallback

**Result**: CloudForge always works, AWS MCP integration is optional enhancement

## Docker Deployment

When running in Docker (docker-compose):

```yaml
# docker-compose.yml
services:
  api:
    environment:
      - CLOUDFORGE_AWS_MCP_ENABLED=0  # Disable if uvx not installed in Docker
    # Or enable if uvx is available
    # - CLOUDFORGE_AWS_MCP_ENABLED=1
```

To enable AWS MCP in Docker:
1. Ensure `uv` is installed in Dockerfile
2. Set `CLOUDFORGE_AWS_MCP_ENABLED=1`
3. Allow extra startup time for MCP servers to initialize

## Benefits

### For Architecture Teams

- **Real-time AWS Best Practices** embedded in generated diagrams
- **Compliance-ready** architectures following AWS recommendations
- **Automated Optimization** suggestions built into blueprint analysis
- **Learning Opportunity** - See AWS best practices in action

### For CloudForge

- **Enhanced Quality** - AWS-validated architecture patterns
- **Differentiation** - Unique integration with AWS Labs MCP servers
- **Extensibility** - Easy to add more MCP servers (CI/CD, Security, etc.)
- **Future-ready** - Prepared for expanding MCP ecosystem

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'awslabs'"

**Solution**: Install AWS MCP servers or disable integration
```bash
pip install awslabs.aws-diagram-mcp-server
pip install awslabs.aws-documentation-mcp-server
```

Or set:
```bash
export CLOUDFORGE_AWS_MCP_ENABLED=0
```

### Issue: MCP Server doesn't start (timeout)

**Solution**: Check logs and verify `uvx` is installed
```bash
which uvx
uvx --version
```

If missing, install `uv`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Issue: AWS Documentation not enriching prompts

**Solution**: Check logging level
```bash
export FASTMCP_LOG_LEVEL=DEBUG
docker-compose up
```

## Future Enhancements

Potential extensions of AWS MCP integration:

1. **AWS Security Best Practices** - Add security MCP server
2. **AWS Cost Optimization** - Add cost analyzer MCP server
3. **AWS Well-Architected Framework** - Validate against 5 pillars
4. **Multi-region Support** - Enhanced prompts for global architectures
5. **Diagram Comparison** - Compare CloudForge vs AWS server outputs
6. **Interactive Refinement** - Let users ask AWS-specific questions

## References

- [AWS Blog: Build AWS architecture diagrams using Amazon Q CLI and MCP](https://aws.amazon.com/blogs/machine-learning/build-aws-architecture-diagrams-using-amazon-q-cli-and-mcp/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [AWS Diagram MCP Server](https://github.com/awslabs/aws-diagram-mcp-server)
- [AWS Documentation MCP Server](https://github.com/awslabs/aws-documentation-mcp-server)
