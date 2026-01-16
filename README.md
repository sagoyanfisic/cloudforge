# AWS Diagram MCP Server (Extended)

Una extensión mejorada del MCP Server oficial de AWS para generar diagramas de arquitectura con validación y almacenamiento integrado.

## Características

✨ **Generación de Diagramas AWS**
- Crear diagramas de arquitectura usando Python DSL
- Soporte para múltiples formatos (PNG, PDF, SVG)
- Componentes AWS prevalidados

🔍 **Validación de Diagramas**
- Validación de sintaxis Python
- Verificación de componentes AWS válidos
- Análisis de seguridad del código
- Límites configurables (componentes, relaciones)

💾 **Almacenamiento Persistente**
- Guardar diagramas generados
- Organización con etiquetas
- Búsqueda y filtrado
- Historial de cambios con timestamps
- Checksums SHA256 para integridad

## Instalación

### Requisitos Previos

- Python 3.10+
- GraphViz (para la generación de diagramas)
- uv (gestor de paquetes de Astral)

### MacOS

```bash
# Instalar GraphViz
brew install graphviz

# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clonar el repositorio
cd /Users/yancelsalinas/Documents/claude-code/mcp-aws

# Instalar dependencias
uv pip install -e .
```

### Docker

```bash
docker build -t aws-diagram-mcp .
docker run -it aws-diagram-mcp
```

## Uso

### 1. Generar un Diagrama

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

### 2. Validar Código

Antes de generar un diagrama, valida el código:

- **Sintaxis**: Se verifica que el código Python sea válido
- **Componentes**: Se validan los componentes AWS utilizados
- **Seguridad**: Se detectan funciones peligrosas (exec, eval, etc.)
- **Límites**: Se verifica el número máximo de componentes y relaciones

### 3. Almacenar Diagramas

Los diagramas se almacenan automáticamente en:
```
~/.aws_diagrams/
├── diagrams/          # Archivos de salida (PNG, PDF, SVG)
├── metadata/          # Información de metadatos
└── index.json         # Índice de diagramas
```

### 4. Gestionar Diagramas Guardados

**Listar diagramas:**
```bash
aws-diagram list
```

**Filtrar por etiqueta:**
```bash
aws-diagram list --tag production
```

**Obtener detalles:**
```bash
aws-diagram get <diagram_id>
```

**Eliminar:**
```bash
aws-diagram delete <diagram_id>
```

## Configuración

### Variables de Entorno

```bash
# Ruta de almacenamiento
AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH=/custom/path

# Tamaño máximo (MB)
AWS_DIAGRAM_MAX_DIAGRAM_SIZE_MB=100

# Formatos de salida
AWS_DIAGRAM_OUTPUT_FORMATS=png,pdf,svg

# Límites de validación
AWS_DIAGRAM_MAX_COMPONENTS=100
AWS_DIAGRAM_MAX_RELATIONSHIPS=200

# Nivel de logging
AWS_DIAGRAM_LOG_LEVEL=INFO
```

### Archivo de Configuración

Crear `~/.aws_diagrams/config.yaml`:

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

## API MCP Tools

### 1. `generate_diagram`

Genera un diagrama a partir de código Python.

**Parámetros:**
- `code` (string, requerido): Código Python con DSL de diagrams
- `name` (string, requerido): Nombre del diagrama
- `description` (string, opcional): Descripción
- `validate` (boolean, opcional): Validar antes de generar (default: true)

**Respuesta:**
- `success`: Booleano indicando éxito
- `diagram_id`: ID único del diagrama
- `file_path`: Ruta del archivo generado
- `output_formats`: Formatos disponibles

### 2. `validate_diagram`

Valida el código de un diagrama sin generarlo.

**Parámetros:**
- `code` (string, requerido): Código Python a validar

**Respuesta:**
- `is_valid`: Booleano de validación
- `errors`: Lista de errores
- `warnings`: Lista de advertencias
- `component_count`: Número de componentes
- `relationship_count`: Número de relaciones

### 3. `save_diagram`

Guarda un diagrama con metadatos y etiquetas.

**Parámetros:**
- `diagram_id` (string, requerido): ID del diagrama a guardar
- `tags` (array, opcional): Etiquetas para organización

### 4. `list_diagrams`

Lista todos los diagramas guardados.

**Parámetros:**
- `tag` (string, opcional): Filtrar por etiqueta

**Respuesta:**
- Array de diagramas con metadatos

### 5. `get_diagram`

Obtiene un diagrama específico con detalles completos.

**Parámetros:**
- `diagram_id` (string, requerido): ID del diagrama

### 6. `delete_diagram`

Elimina un diagrama guardado.

**Parámetros:**
- `diagram_id` (string, requerido): ID del diagrama a eliminar

## Tests

Ejecutar los tests:

```bash
# Todos los tests
pytest -xvs tests/

# Tests específicos
pytest -xvs tests/test_validator.py
pytest -xvs tests/test_storage.py

# Con cobertura
pytest --cov=src --cov-report=html tests/
```

## Componentes AWS Soportados

### Compute
- `Lambda` - AWS Lambda
- `EC2` - Amazon EC2
- `ECS` - Amazon ECS
- `EKS` - Amazon EKS
- `AutoScaling` - Auto Scaling

### Networking
- `APIGateway` - API Gateway
- `Route53` - Route 53
- `CloudFront` - CloudFront
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

## Ejemplos

### Ejemplo 1: Arquitectura Serverless

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

### Ejemplo 2: Arquitectura con Microservicios

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

### Ejemplo 3: Multi-Region

```python
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb

with Diagram("Multi-Region Setup", show=False):
    with Cluster("US-EAST-1"):
        us_lambda = Lambda("Function")
        us_db = Dynamodb("Database")
        us_lambda >> us_db

    with Cluster("EU-WEST-1"):
        eu_lambda = Lambda("Function")
        eu_db = Dynamodb("Database")
        eu_lambda >> eu_db

    us_db >> eu_db
```

## 🎨 Ejemplo Completo: Arquitectura Multi-Región

A continuación se muestra un ejemplo completo que genera un diagrama profesional de arquitectura multi-región con DNS global, CDN y servicios distribuidos:

### Código Python

```python
import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda, EC2
from diagrams.aws.database import Dynamodb, RDS
from diagrams.aws.network import Route53, CloudFront

# Asegurar que el directorio de salida existe
os.makedirs("examples", exist_ok=True)

with Diagram(
    "Multi-Region Application",
    show=False,
    filename="examples/multi_region",
    direction="TB"
):
    # Servicios globales
    dns = Route53("Global DNS")
    cdn = CloudFront("CloudFront CDN")

    # Región US-EAST-1
    with Cluster("US-EAST-1"):
        with Cluster("Compute"):
            us_lambda = Lambda("Lambda")
            us_ec2 = EC2("EC2 Instances")

        with Cluster("Storage"):
            us_db = Dynamodb("DynamoDB")
            us_rds = RDS("RDS Primary")

    # Región EU-WEST-1
    with Cluster("EU-WEST-1"):
        with Cluster("Compute"):
            eu_lambda = Lambda("Lambda")
            eu_ec2 = EC2("EC2 Instances")

        with Cluster("Storage"):
            eu_db = Dynamodb("DynamoDB")
            eu_rds = RDS("RDS Replica")

    # Conexiones globales
    dns >> [cdn, us_lambda, eu_lambda]

    # Relaciones regionales
    us_lambda >> us_ec2
    us_ec2 >> us_db
    us_rds >> eu_rds

    eu_lambda >> eu_ec2
    eu_ec2 >> eu_db

    # Replicación cross-region
    us_db >> eu_db

print("✅ Diagrama generado: examples/multi_region.png")
```

### Diagrama Resultante

El código anterior genera una arquitectura profesional que incluye:

- **DNS Global**: Route53 como punto de entrada global
- **CDN**: CloudFront para distribución de contenido
- **Compute distribuido**: Lambda y EC2 en dos regiones
- **Persistencia**: DynamoDB y RDS en ambas regiones
- **Replicación**: Sincronización entre regiones

**Formatos de salida generados:**
- `multi_region.png` - Imagen raster (predeterminado)
- `multi_region.pdf` - Formato vectorial (si está habilitado)
- `multi_region.svg` - Gráficos vectoriales escalables (si está habilitado)

### Ejecutar el Ejemplo

```bash
# Localmente
python examples/multi_region.py

# Con Docker
docker run -v $(pwd)/examples:/app/examples cloudforge:latest \
  python examples/multi_region.py
```

## Troubleshooting

### Error: "GraphViz not found"

```bash
# MacOS
brew install graphviz

# Linux (Ubuntu/Debian)
sudo apt-get install graphviz

# Linux (Fedora)
sudo dnf install graphviz
```

### Error: "Module not found: diagrams"

```bash
uv pip install diagrams
```

### Validación falla con componentes válidos

Verifica que uses los nombres exactos de los componentes y la ruta correcta:
```python
# Correcto ✓
from diagrams.aws.compute import Lambda

# Incorrecto ✗
from diagrams.aws.compute import lambda
```

## Desarrollo

### Setup del Entorno

```bash
# Instalar dependencias de desarrollo
uv pip install -e ".[dev]"

# Ejecutar tests
pytest -xvs tests/

# Verificar formato con black
black src/ tests/

# Linting con ruff
ruff check src/ tests/

# Type checking
mypy src/
```

## Estructura del Proyecto

```
mcp-aws/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuración
│   ├── models.py          # Modelos de datos
│   ├── validator.py       # Validación de diagramas
│   ├── generator.py       # Generación de diagramas
│   ├── storage.py         # Almacenamiento persistente
│   └── server.py          # Servidor MCP
├── tests/
│   ├── test_validator.py
│   ├── test_storage.py
│   └── test_generator.py
├── Dockerfile
├── pyproject.toml
├── README.md
└── LICENSE
```

## Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## Soporte

Para reportar problemas o sugerencias, por favor abre un issue en el repositorio.

## Changelog

### v0.1.0 (2026-01-14)
- ✨ Inicial release
- ✨ Generación de diagramas AWS
- ✨ Validación con análisis de seguridad
- ✨ Almacenamiento persistente con metadatos
- ✨ API MCP completa
- ✨ Tests comprensivos
- ✨ Dockerfile con Python 3.12

## Roadmap

- [ ] Soporte para más tipos de diagramas (Sequence, Flow)
- [ ] Exportación a Terraform
- [ ] Integración con AWS CLI
- [ ] Web UI para visualización
- [ ] Integración con Git para versionado
- [ ] Colaboración en tiempo real
