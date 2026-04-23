# Dockerfile para o backend FastAPI
FROM python:3.12-slim

WORKDIR /app

# Instalar uv
RUN pip install uv

# Copiar dependências
COPY pyproject.toml .

# Instalar dependências de produção
RUN uv sync --no-dev

# Copiar código
COPY . .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
