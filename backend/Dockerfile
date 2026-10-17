# syntax=docker/dockerfile:1

# Etapa 1: instala as dependências de produção em um ambiente virtual
FROM python:3.14-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9.10 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-dev --no-install-project

# Etapa 2: imagem final, sem o uv nem ferramentas de desenvolvimento
FROM python:3.14-slim

# O pip não é usado em produção e traz dependências próprias com vulnerabilidades conhecidas
RUN pip uninstall --yes --no-cache-dir pip \
    && groupadd --system app \
    && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app app ./app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
