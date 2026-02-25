# Multi-stage: build deps then run (one image for all Python services)
FROM python:3.12-slim as builder
WORKDIR /app
RUN pip install --no-cache-dir wheel
COPY pyproject.toml .
RUN pip wheel --no-deps -w /wheels .

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*
COPY libs ./libs
COPY services ./services
COPY scripts ./scripts
COPY alembic.ini .

# Default: run orchestrator (override in compose)
CMD ["uvicorn", "services.orchestrator_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
