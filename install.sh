#!/bin/bash

# AWS Diagram MCP Server - Installation Script

set -e

echo "🚀 AWS Diagram MCP Server - Installation"
echo "========================================"

# Detect OS
OS="$(uname -s)"

# Install GraphViz based on OS
echo "📦 Checking GraphViz installation..."
if ! command -v dot &> /dev/null; then
    echo "Installing GraphViz..."
    if [[ "$OS" == "Darwin" ]]; then
        echo "🍎 Installing for macOS..."
        if ! command -v brew &> /dev/null; then
            echo "❌ Homebrew not found. Please install Homebrew first: https://brew.sh"
            exit 1
        fi
        brew install graphviz
    elif [[ "$OS" == "Linux" ]]; then
        echo "🐧 Installing for Linux..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y graphviz
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y graphviz
        else
            echo "❌ Unsupported package manager. Please install GraphViz manually."
            exit 1
        fi
    else
        echo "❌ Unsupported OS. Please install GraphViz manually: https://www.graphviz.org/"
        exit 1
    fi
    echo "✅ GraphViz installed successfully"
else
    echo "✅ GraphViz is already installed"
fi

# Check if uv is installed
echo ""
echo "🔍 Checking uv installation..."
if ! command -v uv &> /dev/null; then
    echo "📥 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ uv installed successfully"
else
    echo "✅ uv is already installed"
fi

# Install project dependencies
echo ""
echo "📚 Installing project dependencies..."
uv pip install -e .

# Install development dependencies
echo ""
echo "🛠️  Installing development dependencies..."
uv pip install -e ".[dev]"

# Create storage directory
echo ""
echo "📁 Creating storage directory..."
mkdir -p ~/.aws_diagrams/diagrams
mkdir -p ~/.aws_diagrams/metadata
echo "✅ Storage directory created"

# Copy example .env
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file (customize as needed)"
else
    echo "✅ .env file already exists"
fi

# Run tests
echo ""
echo "🧪 Running tests to verify installation..."
if bash run_tests.sh; then
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Review and customize .env file if needed"
    echo "2. Run the server: uv run aws-diagram-mcp"
    echo "3. Check examples in examples/ directory"
    echo "4. Read README.md for detailed usage"
else
    echo "❌ Tests failed. Please review the errors above."
    exit 1
fi
