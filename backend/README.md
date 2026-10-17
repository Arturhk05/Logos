# Logos API

API da plataforma Logos, construída com FastAPI.

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (gerenciador de dependências e de versões do Python)

O uv instala automaticamente a versão do Python definida em `.python-version`.

## Configuração

Copie o arquivo de exemplo e ajuste os valores, se necessário:

```bash
cp .env.example .env
```

| Variável | Descrição | Padrão |
|---|---|---|
| `ENVIRONMENT` | Ambiente de execução: `development`, `test` ou `production` | `development` |
| `DATABASE_URL` | URL de conexão com o PostgreSQL | `postgresql+psycopg://logos:logos@localhost:5432/logos` |

## Executar localmente

```bash
uv sync                                   # instala as dependências
uv run uvicorn app.main:app --reload      # sobe a API em http://localhost:8000
```

| URL | Descrição |
|---|---|
| http://localhost:8000/api/health | Verificação de saúde da API |
| http://localhost:8000/api/docs | Documentação interativa (Swagger) |
| http://localhost:8000/api/openapi.json | Especificação OpenAPI |

## Qualidade de código

| Comando | O que faz |
|---|---|
| `uv run ruff check .` | Lint, incluindo regras de segurança (Bandit) |
| `uv run ruff check . --fix` | Lint, corrigindo automaticamente o que for possível |
| `uv run ruff format .` | Formata o código |
| `uv run ruff format --check .` | Verifica a formatação sem alterar arquivos |
| `uv run mypy app` | Verificação de tipos (modo strict) |

## Dependências

| Comando | O que faz |
|---|---|
| `uv add <pacote>` | Adiciona uma dependência de produção |
| `uv add --dev <pacote>` | Adiciona uma dependência de desenvolvimento |
| `uv sync --no-dev` | Instala apenas as dependências de produção |
