# Quick Start Guide

¡Bienvenido a AWS Diagram MCP Server! Esta guía te ayudará a comenzar en 5 minutos.

## 1. Instalación Rápida (macOS)

```bash
# Clonar o navegar al directorio
cd /Users/yancelsalinas/Documents/claude-code/mcp-aws

# Ejecutar script de instalación
chmod +x install.sh
./install.sh
```

## 2. Configuración Básica

El script de instalación crea automáticamente:
- ✅ Directorio de almacenamiento: `~/.aws_diagrams`
- ✅ Archivo `.env` con configuración por defecto
- ✅ Dependencias del proyecto

## 3. Primer Diagrama

Crea un archivo `my_diagram.py`:

```python
from diagrams import Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway

with Diagram("My First Diagram", show=False):
    api = APIGateway("API")
    fn = Lambda("Function")
    db = Dynamodb("Database")

    api >> fn >> db
```

## 4. Generar el Diagrama

```bash
# Ejecutar el archivo Python
python my_diagram.py

# El archivo PNG se generará en el directorio actual
```

## 5. Usar con MCP

### Opción A: Cliente MCP (Cursor, VS Code, etc.)

Agregar a tu configuración MCP:

```json
{
  "mcpServers": {
    "aws-diagram-mcp": {
      "command": "uv",
      "args": ["run", "aws-diagram-mcp"],
      "env": {
        "AWS_DIAGRAM_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Opción B: Docker

```bash
# Construir la imagen
docker build -t aws-diagram-mcp .

# Ejecutar
docker run -it \
  -v ~/.aws_diagrams:/data/diagrams \
  aws-diagram-mcp
```

## 6. Ejemplos Incluidos

```bash
# Ver diagramas de ejemplo
python examples/serverless_app.py
python examples/microservices.py
python examples/multi_region.py

# Los archivos PNG se generarán en el directorio actual
```

## 7. Validar Diagramas

```python
from src.validator import DiagramValidator

code = """
from diagrams import Diagram
from diagrams.aws.compute import Lambda
with Diagram("Test", show=False):
    fn = Lambda("Function")
"""

validator = DiagramValidator()
result = validator.validate(code)

print(f"Valid: {result.is_valid}")
print(f"Components: {result.component_count}")
print(f"Errors: {result.errors}")
```

## 8. Almacenar Diagramas

```python
from src.storage import DiagramStorage
from src.models import DiagramMetadata, DiagramType

storage = DiagramStorage()

metadata = DiagramMetadata(
    name="My Diagram",
    description="A beautiful diagram",
    diagram_type=DiagramType.AWS_ARCHITECTURE,
    tags=["production", "web"]
)

stored = storage.save_diagram(code, metadata, output_files)
print(f"Diagram saved with ID: {stored.diagram_id}")

# Listar diagramas
diagrams = storage.list_diagrams()
for d in diagrams:
    print(f"- {d.metadata.name} ({d.diagram_id})")
```

## 9. Comandos Útiles

```bash
# Ejecutar tests
bash run_tests.sh

# Tests con coverage
pytest --cov=src --cov-report=html tests/

# Linting
ruff check src/ tests/

# Formatear código
black src/ tests/

# Type checking
mypy src/

# Instalar paquetes adicionales
uv pip install <package-name>
```

## 10. Estructura de Directorios

```
mcp-aws/
├── src/                    # Código fuente
│   ├── config.py          # Configuración
│   ├── models.py          # Modelos de datos
│   ├── validator.py       # Validador
│   ├── generator.py       # Generador
│   ├── storage.py         # Almacenamiento
│   └── server.py          # Servidor MCP
├── tests/                 # Tests
│   ├── test_validator.py
│   └── test_storage.py
├── examples/              # Ejemplos
│   ├── serverless_app.py
│   ├── microservices.py
│   └── multi_region.py
├── .env.example          # Ejemplo de configuración
├── Dockerfile            # Docker image
├── pyproject.toml        # Configuración del proyecto
├── README.md             # Documentación completa
└── QUICKSTART.md         # Esta guía
```

## 11. Solución de Problemas

### "GraphViz not found"
```bash
# macOS
brew install graphviz

# Linux (Ubuntu)
sudo apt-get install graphviz
```

### "Module not found: diagrams"
```bash
uv pip install diagrams
```

### "Permission denied: ./install.sh"
```bash
chmod +x install.sh
./install.sh
```

## 12. Componentes AWS Disponibles

**Compute:**
- Lambda, EC2, ECS, EKS, AutoScaling

**Database:**
- Dynamodb, RDS, ElastiCache

**Networking:**
- APIGateway, Route53, CloudFront, ALB, NLB, ELB

**Storage:**
- S3, Dynamodb

**Integration:**
- SQS, SNS, CodePipeline, CodeBuild, CodeDeploy

**Management:**
- CloudWatch, IAM, KMS

## 13. Ejemplo Completo: API Serverless

```python
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway
from diagrams.aws.integration import SQS

with Diagram("Serverless API", show=False):
    with Cluster("API Layer"):
        gateway = APIGateway("API Gateway")

    with Cluster("Compute"):
        create = Lambda("Create")
        read = Lambda("Read")
        process = Lambda("Process")

    with Cluster("Storage"):
        db = Dynamodb("Database")
        queue = SQS("Queue")

    gateway >> create >> db
    gateway >> read >> db
    create >> queue >> process >> db
```

## 14. Siguientes Pasos

1. 📖 Lee el [README.md](README.md) completo
2. 🔍 Explora los ejemplos en `examples/`
3. 🧪 Ejecuta los tests: `bash run_tests.sh`
4. 🐳 Prueba con Docker si quieres
5. 🚀 Integra con tu cliente MCP favorito

## 15. Recursos Útiles

- [Documentación de Diagrams](https://diagrams.mingrammer.com/)
- [AWS CLI Documentation](https://docs.aws.amazon.com/cli/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [GraphViz](https://www.graphviz.org/)

## 16. Contacto y Soporte

Para reportar issues o sugerencias:
- 🐛 [Reportar un bug](https://github.com/your-repo/issues)
- 💡 [Sugerir una característica](https://github.com/your-repo/issues)
- 📧 Contactar al equipo de desarrollo

---

¡Disfruta creando diagramas AWS! 🎉
