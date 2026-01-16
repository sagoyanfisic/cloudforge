FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    procps \
    graphviz \
    && rm -rf /var/lib/apt/lists/*


ADD https://astral.sh/uv/0.8.13/install.sh /tmp/uv-installer.sh

RUN sh /tmp/uv-installer.sh && rm /tmp/uv-installer.sh

ENV PATH="/root/.local/bin:$PATH"


COPY pyproject.toml uv.lock ./

RUN uv pip install --system --no-cache --compile \
    mcp \
    diagrams \
    pydantic \
    pydantic-settings \
    python-dotenv


RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

COPY --chown=appuser:appuser pyproject.toml uv.lock ./
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser tests ./tests
COPY --chown=appuser:appuser examples ./examples

USER appuser


CMD ["python", "-m", "src"]
