# 🔥 CloudForge

**AI-Powered AWS Architecture Diagrams with Validation & Persistence**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org)
[![Docker](https://img.shields.io/badge/Docker-Yes-brightgreen)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple)](https://modelcontextprotocol.io)

CloudForge is an intelligent MCP server that transforms Python code into professional AWS architecture diagrams with built-in validation and persistent storage.

## ✨ Features

### 🎨 Diagram Generation
- Create AWS architecture diagrams from Python code
- Support for 50+ AWS components (EC2, Lambda, RDS, S3, etc.)
- Multiple output formats: PNG, PDF, SVG
- Professional visualization with GraphViz

### ✓ Intelligent Validation
- Python syntax validation using AST parsing
- AWS component whitelisting
- Security scanning (detects dangerous functions)
- Component relationship analysis
- Configurable limits (components, relationships)

### 💾 Persistent Storage
- Save diagrams with metadata
- Tag-based organization and filtering
- SHA256 checksum verification
- JSON-based indexing for fast retrieval
- Full CRUD operations

### 🔍 Multi-Account Architecture Support
- Hub-and-spoke patterns
- PrivateLink connectivity
- Cross-region deployments
- Centralized monitoring

### 📊 Enterprise Ready
- FastMCP implementation (modern MCP protocol)
- Pydantic data validation
- Docker containerization with UV package manager
- Comprehensive logging and error handling

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- GraphViz (diagram rendering engine)
- Docker (optional)

### macOS Installation

```bash
# Install GraphViz
brew install graphviz

# Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
cd /Users/yancelsalinas/Documents/claude-code/mcp-aws

# Install dependencies
uv pip install -e .
```

### Docker Installation

```bash
# Build image
docker build -t cloudforge:latest .

# Run container
docker run -it cloudforge:latest python -m src
```

## 📖 Usage Guide

### 1. Generate a Diagram

```python
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway

with Diagram("Serverless App", show=False):
    api = APIGateway("API Gateway")
    function = Lambda("Function")
    database = Dynamodb("DynamoDB")

    api >> function >> database
```

### 2. Validate Diagram Code

Before generating, validate your diagram code:

- **Syntax**: Verifies valid Python code
- **Components**: Validates AWS service names
- **Security**: Detects dangerous functions (exec, eval, etc.)
- **Limits**: Enforces max components and relationships

### 3. Store Diagrams

Diagrams are automatically stored in:
```
~/.aws_diagrams/
├── diagrams/          # Output files (PNG, PDF, SVG)
├── metadata/          # Metadata information
└── index.json         # Diagram index
```

### 4. Manage Saved Diagrams

**List diagrams:**
```bash
aws-diagram list
```

**Filter by tag:**
```bash
aws-diagram list --tag production
```

**Get details:**
```bash
aws-diagram get <diagram_id>
```

**Delete:**
```bash
aws-diagram delete <diagram_id>
```

## ⚙️ Configuration

### Environment Variables

```bash
# Storage path
AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH=/custom/path

# Max file size (MB)
AWS_DIAGRAM_MAX_DIAGRAM_SIZE_MB=100

# Output formats
AWS_DIAGRAM_OUTPUT_FORMATS=png,pdf,svg

# Validation limits
AWS_DIAGRAM_MAX_COMPONENTS=100
AWS_DIAGRAM_MAX_RELATIONSHIPS=200

# Logging level
AWS_DIAGRAM_LOG_LEVEL=INFO
```

### Configuration File

Create `~/.aws_diagrams/config.yaml`:

```yaml
storage:
  path: ~/.aws_diagrams
  max_size_mb: 50

validation:
  enabled: true
  max_components: 100
  max_relationships: 200

output:
  formats:
    - png
    - pdf
    - svg
```

## 🔌 MCP Tools

### 1. `generate_diagram`

Generate an AWS architecture diagram from Python code.

**Parameters:**
- `code` (string, required): Python code using diagrams DSL
- `name` (string, required): Diagram name
- `description` (string, optional): Diagram description
- `validate` (boolean, optional): Validate before generating (default: true)

**Response:**
```json
{
  "success": true,
  "message": "Diagram generated successfully",
  "output_files": {
    "png": "/path/to/diagram.png",
    "pdf": "/path/to/diagram.pdf"
  }
}
```

### 2. `validate_diagram`

Validate diagram code without generating output.

**Parameters:**
- `code` (string, required): Python code to validate

**Response:**
```json
{
  "is_valid": true,
  "component_count": 5,
  "relationship_count": 4,
  "errors": [],
  "warnings": []
}
```

### 3. `list_diagrams`

List all saved diagrams.

**Parameters:**
- `tag` (string, optional): Filter by tag

### 4. `get_diagram`

Get specific diagram details.

**Parameters:**
- `diagram_id` (string, required): Diagram ID

### 5. `delete_diagram`

Delete a saved diagram.

**Parameters:**
- `diagram_id` (string, required): Diagram ID to delete

## 📚 Examples

### Example 1: Serverless Architecture

```python
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway
from diagrams.aws.integration import SQS

with Diagram("Serverless Architecture", show=False):
    client = APIGateway("Client")
    api = APIGateway("API Gateway")
    lambda_fn = Lambda("Lambda Handler")
    queue = SQS("Job Queue")
    processor = Lambda("Job Processor")
    db = Dynamodb("DynamoDB")

    client >> api >> lambda_fn
    lambda_fn >> queue >> processor >> db
```

### Example 2: Microservices Architecture

```python
from diagrams import Diagram, Cluster
from diagrams.aws.compute import ECS
from diagrams.aws.network import ALB, Route53
from diagrams.aws.database import RDS

with Diagram("Microservices Architecture", show=False):
    dns = Route53("DNS")
    lb = ALB("Load Balancer")

    with Cluster("Services"):
        service1 = ECS("Service 1")
        service2 = ECS("Service 2")

    with Cluster("Data"):
        db1 = RDS("Primary DB")
        db2 = RDS("Replica DB")

    dns >> lb >> [service1, service2]
    service1 >> db1
    service2 >> db1 >> db2
```

### Example 3: Multi-Region Architecture

![Multi-Region Application Architecture](images/multi-region-example.png)

```python
import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda, EC2
from diagrams.aws.database import Dynamodb, RDS
from diagrams.aws.network import Route53, CloudFront

os.makedirs("examples", exist_ok=True)

with Diagram(
    "Multi-Region Application",
    show=False,
    filename="examples/multi_region",
    direction="TB"
):
    # Global services
    dns = Route53("Global DNS")
    cdn = CloudFront("CloudFront CDN")

    # US-EAST-1 Region
    with Cluster("US-EAST-1"):
        with Cluster("Compute"):
            us_lambda = Lambda("Lambda")
            us_ec2 = EC2("EC2 Instances")

        with Cluster("Storage"):
            us_db = Dynamodb("DynamoDB")
            us_rds = RDS("RDS Primary")

    # EU-WEST-1 Region
    with Cluster("EU-WEST-1"):
        with Cluster("Compute"):
            eu_lambda = Lambda("Lambda")
            eu_ec2 = EC2("EC2 Instances")

        with Cluster("Storage"):
            eu_db = Dynamodb("DynamoDB")
            eu_rds = RDS("RDS Replica")

    # Global routing
    dns >> [cdn, us_lambda, eu_lambda]

    # Regional relationships
    us_lambda >> us_ec2
    us_ec2 >> us_db
    us_rds >> eu_rds

    eu_lambda >> eu_ec2
    eu_ec2 >> eu_db

    # Cross-region replication
    us_db >> eu_db

print("✅ Diagram generated: examples/multi_region.png")
```

**Run the example:**

```bash
# Locally
python examples/multi_region.py

# Docker
docker run -v $(pwd)/examples:/app/examples cloudforge:latest \
  python examples/multi_region.py
```

## 🏗️ Environment Setup

### Development Installation

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Verify installation
python -c "import src; print(f'CloudForge v{src.__version__}')"
```

### Project Structure

```
cloudforge/
├── src/
│   ├── __init__.py          # Package metadata & entry point
│   ├── server.py            # FastMCP server implementation
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic data models
│   ├── validator.py         # Diagram validation
│   ├── generator.py         # Diagram generation engine
│   └── storage.py           # Persistent storage layer
├── tests/
│   ├── test_validator.py    # Validator tests
│   ├── test_storage.py      # Storage tests
│   └── test_generator.py    # Generator tests
├── examples/
│   ├── serverless_app.py
│   ├── microservices.py
│   ├── multi_region.py
│   ├── aws_hub_spoke.py
│   └── multi_account_thanos.py
├── images/
│   ├── README.md
│   └── multi-region-example.png
├── .dockerignore             # Docker build optimization
├── Dockerfile               # Container configuration
├── pyproject.toml           # Project metadata
├── uv.lock                  # Dependency lock file
└── README.md                # This file
```

## 🧪 Testing

### Run All Tests

```bash
# Execute all tests
pytest -xvs tests/

# Run with coverage
pytest --cov=src --cov-report=html tests/

# Run specific test file
pytest -xvs tests/test_validator.py
pytest -xvs tests/test_storage.py
```

### Test Coverage

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html tests/

# View coverage
open htmlcov/index.html
```

### Code Quality

```bash
# Format with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

## 📋 Supported AWS Components

### Compute
- `Lambda` - AWS Lambda
- `EC2` - Amazon EC2
- `ECS` - Amazon ECS
- `EKS` - Amazon EKS
- `AutoScaling` - Auto Scaling

### Networking
- `APIGateway` - API Gateway
- `Route53` - Route 53
- `CloudFront` - CloudFront CDN
- `VPC` - VPC
- `SecurityGroup` - Security Groups
- `ELB`, `ALB`, `NLB` - Load Balancers

### Storage
- `S3` - Amazon S3
- `Dynamodb` - DynamoDB
- `RDS` - RDS Database
- `ElastiCache` - ElastiCache

### Integration
- `SQS` - SQS Queue
- `SNS` - SNS Topic
- `CodePipeline` - CodePipeline
- `CodeBuild` - CodeBuild
- `CodeDeploy` - CodeDeploy

### Management
- `CloudWatch` - CloudWatch
- `IAM` - IAM
- `KMS` - KMS

## 🔧 Troubleshooting

### "GraphViz not found"

```bash
# macOS
brew install graphviz

# Linux (Ubuntu/Debian)
sudo apt-get install graphviz

# Linux (Fedora)
sudo dnf install graphviz

# Windows (Chocolatey)
choco install graphviz
```

### "Module not found: diagrams"

```bash
uv pip install diagrams
```

### Validation fails with valid components

Verify you're using exact component names and correct import paths:

```python
# ✓ Correct
from diagrams.aws.compute import Lambda

# ✗ Incorrect
from diagrams.aws.compute import lambda
```

### Docker build issues

```bash
# Clean rebuild
docker build --no-cache -t cloudforge:latest .

# Check image size
docker images cloudforge:latest
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

### Contributing Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation
- Keep commits atomic and descriptive

## 📝 Changelog

### v0.1.0 (2026-01-16)

**✨ Features:**
- Initial release
- AWS architecture diagram generation
- Intelligent diagram validation with security analysis
- Persistent storage with metadata management
- Complete MCP API implementation
- Multi-account architecture support
- 5 ready-to-use examples

**🔧 Technical:**
- FastMCP server implementation
- Pydantic data validation
- Dockerfile with Python 3.12-slim
- UV package manager integration
- Comprehensive test coverage
- SHA256 checksum verification

**📦 Components:**
- Validator module with AST parsing
- Generator module with subprocess execution
- Storage module with JSON indexing
- Server module with 5 MCP tools

## 🗺️ Roadmap

### Phase 1: Core Features (Completed)
- [x] Diagram generation from Python code
- [x] Validation with security scanning
- [x] Persistent storage with metadata
- [x] MCP server implementation
- [x] Docker support with UV

### Phase 2: Enhancements (In Progress)
- [ ] Support for additional diagram types (Sequence, Flow, Class)
- [ ] Terraform code generation from diagrams
- [ ] AWS CLI integration
- [ ] Web UI for visualization
- [ ] Real-time collaboration features

### Phase 3: Advanced Features (Planned)
- [ ] Git integration for version control
- [ ] AI-powered architecture suggestions
- [ ] Cost estimation from diagrams
- [ ] Security posture analysis
- [ ] Architecture compliance checking

### Phase 4: Integration (Future)
- [ ] CloudFormation template generation
- [ ] Terraform module creation
- [ ] Ansible playbook generation
- [ ] Kubernetes manifest generation

## 💬 Support

### Getting Help

- **Documentation**: See [CLOUDFORGE.md](CLOUDFORGE.md) for comprehensive documentation
- **Issues**: Report bugs on [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: Start a discussion on [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: contact@cloudforge.dev

### FAQ

**Q: Can I use CloudForge for production diagrams?**
A: Yes! CloudForge generates publication-ready diagrams with multiple output formats.

**Q: What's the maximum diagram complexity?**
A: Default limit is 100 components and 200 relationships (configurable).

**Q: Does CloudForge support custom AWS components?**
A: Currently supports 50+ official AWS components. Custom components coming soon.

**Q: Can I export diagrams as IaC?**
A: Terraform export is on the roadmap for Phase 2.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [Diagrams](https://diagrams.mingrammer.com/)
- Powered by [Model Context Protocol](https://modelcontextprotocol.io)
- Uses [FastMCP](https://github.com/modelcontextprotocol/python-sdk)
- Package management by [UV](https://astral.sh/uv/)

---

**CloudForge** - Forge your cloud architecture with AI ⚡

[![Stars](https://img.shields.io/github/stars/your-repo?style=social)](https://github.com/your-repo)
[![Follow](https://img.shields.io/twitter/follow/cloudforge_dev?style=social)](https://twitter.com/cloudforge_dev)
