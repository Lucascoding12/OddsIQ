FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files first so Docker can cache this layer
COPY pyproject.toml uv.lock* ./

# Install dependencies (no dev extras)
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Run DB migrations then start the server.
# Railway injects $PORT; fall back to 8000 for local use.
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 5"]
