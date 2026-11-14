# TerraPulse API. Build from the backend/ directory:  docker build -t terrapulse-api .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen
COPY terrapulse ./terrapulse
COPY data/processed ./data/processed
EXPOSE 8000
CMD ["uv", "run", "--no-dev", "uvicorn", "terrapulse.api:app", "--host", "0.0.0.0", "--port", "8000"]
