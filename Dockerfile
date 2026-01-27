# CloudForge Multi-stage Build
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies directly (not --user)
RUN pip install --no-cache-dir -e .

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (graphviz for diagrams)
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy site-packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create directories for diagrams BEFORE changing user
RUN mkdir -p /app/diagrams /app/diagrams/diagrams /app/diagrams/metadata && \
    chmod -R 777 /app/diagrams

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    mkdir -p /home/appuser/.aws_diagrams && \
    chown -R appuser:appuser /app /home/appuser

USER appuser

# Default to running the MCP server
CMD ["python", "-m", "src"]
