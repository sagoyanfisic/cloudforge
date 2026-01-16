# Docker Setup Guide

Esta guía te ayudará a ejecutar AWS Diagram MCP Server en Docker.

## 📋 Requisitos Previos

- Docker Desktop instalado (macOS, Windows)
- O Docker Engine (Linux)
- 2GB de espacio en disco

## 🚀 Construcción de la Imagen

### Opción 1: Script Automático

```bash
chmod +x build.sh
./build.sh
```

### Opción 2: Construcción Manual

```bash
docker build -t aws-diagram-mcp:latest .
```

### Opción 3: Construcción sin caché (si hay problemas)

```bash
docker build --no-cache -t aws-diagram-mcp:latest .
```

## ▶️ Ejecutar el Servidor

### Opción 1: Docker Run Directo

```bash
# Con volumen para persistencia
docker run -it \
  -v ~/.aws_diagrams:/home/appuser/.aws_diagrams \
  -e AWS_DIAGRAM_LOG_LEVEL=INFO \
  aws-diagram-mcp:latest
```

### Opción 2: Docker Compose (Recomendado)

```bash
# Construcción e inicio
docker-compose up --build

# Solo iniciar (si ya está construido)
docker-compose up

# En background
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## 📊 Verificar que funciona

```bash
# Ver contenedor en ejecución
docker ps

# Ver logs
docker logs aws-diagram-mcp-server

# Acceder al contenedor
docker exec -it aws-diagram-mcp-server /bin/bash
```

## 💾 Persistencia de Datos

Los diagramas se guardan en un volumen Docker. Hay dos formas de acceder:

### Con docker-compose:

```bash
# Ver archivos guardados
docker volume ls
docker volume inspect mcp-aws_diagrams_data
```

### Con docker run:

```bash
# Montar en directorio local
docker run -it \
  -v ~/my_diagrams:/home/appuser/.aws_diagrams \
  aws-diagram-mcp:latest
```

Luego los archivos estarán en `~/my_diagrams/`.

## 🔧 Variables de Entorno

Puedes personalizar el comportamiento con variables de entorno:

```bash
docker run -it \
  -e AWS_DIAGRAM_MAX_COMPONENTS=200 \
  -e AWS_DIAGRAM_MAX_RELATIONSHIPS=400 \
  -e AWS_DIAGRAM_LOG_LEVEL=DEBUG \
  aws-diagram-mcp:latest
```

### Variables disponibles:
- `AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH` - Ruta de almacenamiento
- `AWS_DIAGRAM_MAX_DIAGRAM_SIZE_MB` - Tamaño máximo
- `AWS_DIAGRAM_OUTPUT_FORMATS` - Formatos de salida (comma-separated)
- `AWS_DIAGRAM_MAX_COMPONENTS` - Límite de componentes
- `AWS_DIAGRAM_MAX_RELATIONSHIPS` - Límite de relaciones
- `AWS_DIAGRAM_LOG_LEVEL` - Nivel de logging (DEBUG, INFO, WARNING, ERROR)

## 🐛 Solución de Problemas

### Error: "Could not resolve host: github.com"

Este es un error de conectividad de red durante la construcción. Soluciones:

```bash
# 1. Asegurar que Docker tiene acceso a internet
docker run --rm alpine ping -c 1 google.com

# 2. Reiniciar Docker
# macOS:
killall Docker && open /Applications/Docker.app

# 3. Usar proxy (si estás detrás de uno)
docker build --build-arg HTTP_PROXY=http://proxy:8080 -t aws-diagram-mcp:latest .

# 4. Forzar reintento sin caché
docker build --no-cache -t aws-diagram-mcp:latest .
```

### Error: "Port already in use"

Si el puerto 8000 ya está en uso:

```bash
# Cambiar el puerto en docker-compose.yml:
# ports:
#   - "8001:8000"  # Cambiar 8001 a un puerto libre

# O con docker run:
docker run -it -p 8001:8000 aws-diagram-mcp:latest
```

### El contenedor se detiene inmediatamente

```bash
# Ver logs de error
docker logs aws-diagram-mcp-server

# Ejecutar con modo interactivo para ver errores
docker run -it aws-diagram-mcp:latest
```

### Espacio en disco

```bash
# Limpiar imágenes no usadas
docker image prune

# Limpiar volúmenes no usados
docker volume prune

# Limpiar todo (cuidado)
docker system prune -a
```

## 📦 Inspeccionar la Imagen

```bash
# Ver detalles de la imagen
docker image inspect aws-diagram-mcp:latest

# Ver capas de la imagen
docker image history aws-diagram-mcp:latest

# Ver tamaño
docker images aws-diagram-mcp:latest
```

## 🔐 Seguridad

### El contenedor corre como usuario no-root:

```bash
# Verificar usuario
docker run aws-diagram-mcp:latest whoami
# Output: appuser
```

### Directorios protegidos:

```bash
# Ver permisos
docker run aws-diagram-mcp:latest ls -la /home/appuser/
```

## 📝 Ejemplos de Uso

### Ejecutar con configuración personalizada:

```bash
docker run -it \
  -v ~/my_diagrams:/home/appuser/.aws_diagrams \
  -e AWS_DIAGRAM_LOG_LEVEL=DEBUG \
  -e AWS_DIAGRAM_MAX_COMPONENTS=150 \
  --name my-diagram-server \
  aws-diagram-mcp:latest
```

### Ejecutar múltiples instancias:

```bash
# Instancia 1
docker run -it --name server1 -p 8001:8000 aws-diagram-mcp:latest

# Instancia 2 (en otra terminal)
docker run -it --name server2 -p 8002:8000 aws-diagram-mcp:latest
```

### Conectar desde otra aplicación:

```bash
# Si ambos contenedores están en la misma red:
docker network create aws-diagram
docker run --network aws-diagram --name server aws-diagram-mcp:latest
docker run --network aws-diagram --name client alpine ping server
```

## 🔄 Actualizar la Imagen

Cuando hagas cambios en el código:

```bash
# Opción 1: Reconstruir completamente
docker build --no-cache -t aws-diagram-mcp:latest .

# Opción 2: Solo si cambió el pyproject.toml
docker build -t aws-diagram-mcp:latest .

# Opción 3: Con docker-compose
docker-compose up --build
```

## 📊 Monitoreo

### Ver consumo de recursos:

```bash
docker stats aws-diagram-mcp-server
```

### Ver logs en tiempo real:

```bash
docker logs -f aws-diagram-mcp-server
```

### Acceder a la shell dentro del contenedor:

```bash
docker exec -it aws-diagram-mcp-server bash
```

## 🧹 Limpiar

```bash
# Detener el contenedor
docker-compose down

# Eliminar la imagen
docker rmi aws-diagram-mcp:latest

# Eliminar volumen
docker volume rm mcp-aws_diagrams_data

# Limpiar todo
docker system prune -a
```

## 📚 Comandos Útiles Rápidos

```bash
# Construir
docker build -t aws-diagram-mcp:latest .

# Ejecutar
docker run -it -v ~/.aws_diagrams:/home/appuser/.aws_diagrams aws-diagram-mcp:latest

# Con compose
docker-compose up --build

# Ver contenedores
docker ps -a

# Ver imágenes
docker images

# Ver volúmenes
docker volume ls

# Ver logs
docker logs -f aws-diagram-mcp-server

# Acceder a la shell
docker exec -it aws-diagram-mcp-server bash

# Detener
docker stop aws-diagram-mcp-server

# Eliminar
docker rm aws-diagram-mcp-server
```

## 🆘 Ayuda Adicional

Para más información sobre Docker:
- [Documentación Oficial de Docker](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

Para problemas específicos del proyecto:
- Revisa los logs: `docker logs aws-diagram-mcp-server`
- Accede al contenedor: `docker exec -it aws-diagram-mcp-server bash`
- Verifica la imagen: `docker image inspect aws-diagram-mcp:latest`
