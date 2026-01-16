#!/bin/bash

# AWS Diagram MCP Server - Docker Build Script

set -e

echo "🐳 AWS Diagram MCP Server - Docker Build"
echo "========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Build the image
echo ""
echo "🔨 Building Docker image..."
docker build -t aws-diagram-mcp:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Image built successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Run with Docker: docker run -it aws-diagram-mcp:latest"
    echo "2. Or use docker-compose: docker-compose up"
    echo ""
    echo "🐳 Docker image info:"
    docker images aws-diagram-mcp:latest
else
    echo "❌ Build failed. Check the error messages above."
    exit 1
fi
