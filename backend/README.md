# Logos API

API da plataforma Logos, construída com FastAPI.

## Estrutura do código

O código é organizado por módulos: cada módulo reúne tudo de uma área do negócio (rotas, regras, modelos e acesso a dados).

```
app/
├── main.py            # cria a aplicação FastAPI
├── router.py          # reúne as rotas de todos os módulos sob /api
├── shared/            # código usado por todos os módulos (configuração, banco de dados, erros de domínio)
└── modules/           # um pacote por área do negócio
    ├── auth/
    ├── health/
    ├── incidents/
    └── users/
scripts/               # comandos executados fora da API (ex.: seed dos dados de demonstração)
```

Um módulo pode depender de `shared` e de outros módulos, mas `shared` nunca depende de um módulo.

Dentro de cada módulo, as responsabilidades ficam separadas em camadas:

| Arquivo | Responsabilidade |
|---|---|
| `enums.py` | Valores fixos do domínio (categoria, criticidade, status, papel) |
| `models.py` | Tabelas do banco de dados (SQLAlchemy) |
| `repository.py` | Acesso aos dados, sem regras de negócio |
| `service.py` | Regras de negócio, que usam o repository |

## Pré-requisitos

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (gerenciador de dependências e de versões do Python)
- [Docker](https://docs.docker.com/get-docker/) (para o PostgreSQL local e para executar a aplicação em containers)

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
| `JWT_SECRET` | Segredo que assina os tokens de sessão. Obrigatório em produção, com pelo menos 32 caracteres | segredo fixo, aceito só fora de produção |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | Validade da sessão, em minutos | `480` (8 horas) |

## Contrato da API para o frontend

O frontend gera seus tipos a partir de `frontend/openapi.json`. Sempre que um schema ou uma rota mudar, exporte o contrato e gere os tipos, e commite os dois arquivos junto com a mudança:

```bash
uv run python -m scripts.export_openapi   # a partir de backend/
npm run gen:api                           # a partir de frontend/
```

O CI falha se algum dos dois estiver desatualizado.

## Executar com Docker

Sobe a API e o PostgreSQL, sem precisar do uv nem do Python instalados, e também a interface em http://localhost:8080 (veja o `frontend/README.md`). Execute a partir da raiz do repositório:

| Comando | O que faz |
|---|---|
| `docker compose up -d --build` | Constrói as imagens e sobe banco, API e interface em segundo plano |
| `docker compose up -d --build api` | Sobe só o banco e a API |
| `docker compose ps` | Mostra o estado dos containers (devem aparecer como `healthy`) |
| `docker compose logs -f api` | Acompanha os logs da API |
| `docker compose down` | Para os containers, mantendo os dados |
| `docker compose down -v` | Para os containers e **apaga todos os dados** |

A subida segue esta ordem: o banco fica saudável, o serviço `migrate` aplica as migrations (`alembic upgrade head`), cria os usuários de demonstração que faltarem, cria os incidentes de exemplo se ainda não houver nenhum e termina, e só então a API sobe. Se alguma migration ou o seed falhar, a API não é iniciada (`docker compose logs migrate` mostra o erro).

## Executar para desenvolvimento

Sobe apenas o banco no Docker e a API localmente, com recarga automática ao salvar arquivos:

```bash
docker compose up -d db                   # na raiz do repositório: sobe só o PostgreSQL
uv sync                                   # instala as dependências
uv run alembic upgrade head               # cria ou atualiza as tabelas no banco
uv run python -m scripts.seed             # cria os usuários e incidentes de demonstração (pode rodar de novo sem duplicar)
uv run uvicorn app.main:app --reload      # sobe a API em http://localhost:8000
```

Se a API do Docker estiver rodando, pare-a antes (`docker compose stop api`), pois ela usa a mesma porta `8000`.

| URL | Descrição |
|---|---|
| http://localhost:8000/api/health | Verificação de saúde da API |
| http://localhost:8000/api/docs | Documentação interativa (Swagger) |
| http://localhost:8000/api/openapi.json | Especificação OpenAPI |

## Usuários de demonstração

Criados pelo seed, tanto no Docker quanto no ambiente de desenvolvimento. Todos usam a senha `logos123`:

| Usuário | Papel |
|---|---|
| `camila` | Analista |
| `lucas` | Analista (para demonstrar dois analistas disputando o mesmo incidente) |
| `roberto` | Supervisor |
| `jose` | Motorista |
| `maria`, `antonio`, `paulo` | Motoristas (reportantes dos incidentes de exemplo) |

## Incidentes de exemplo

O seed também cria 140 incidentes, com o mesmo conteúdo em todos os ambientes e datas relativas ao momento em que ele roda: 100 ativos na fila (65 _Abertos_ e 35 _Em Investigação_), como os "100 incidentes simultâneos" do desafio, e 40 encerrados no histórico (28 _Fechados_ e 12 _Inconclusivos_). Cada um tem uma linha do tempo coerente com o seu estado (RN-12): reportado, assumido e, conforme o caso, encerrado, com alguns incidentes em investigação que um supervisor devolveu à fila antes de outro analista assumir. Eles só são criados quando não existe nenhum incidente, então o seed nunca altera nem duplica incidentes que já estejam em uso.

Para recriá-los, **apagando todos os incidentes existentes**:

```bash
uv run python -m scripts.seed --reset-incidents
```

No Docker local, também dá para apagar todos os dados com `docker compose down -v`.

## Qualidade de código

| Comando | O que faz |
|---|---|
| `uv run ruff check .` | Lint, incluindo regras de segurança (Bandit) |
| `uv run ruff check . --fix` | Lint, corrigindo automaticamente o que for possível |
| `uv run ruff format .` | Formata o código |
| `uv run ruff format --check .` | Verifica a formatação sem alterar arquivos |
| `uv run mypy app tests migrations scripts` | Verificação de tipos (modo strict) |

## Migrations do banco de dados

As migrations são gerenciadas pelo [Alembic](https://alembic.sqlalchemy.org/) e ficam em `migrations/versions/`. Os comandos usam o banco definido em `DATABASE_URL`.

| Comando | O que faz |
|---|---|
| `uv run alembic upgrade head` | Aplica todas as migrations pendentes |
| `uv run alembic revision --autogenerate -m "descrição"` | Gera uma migration a partir das mudanças nos modelos |
| `uv run alembic downgrade -1` | Desfaz a última migration |
| `uv run alembic current` | Mostra a migration aplicada no banco |
| `uv run alembic history` | Lista todas as migrations |

Revise sempre a migration gerada antes de commitar: o autogenerate não detecta tudo (por exemplo, renomeação de colunas aparece como remoção e criação). Um teste automatizado falha se algum modelo for alterado sem a migration correspondente.

## Testes

| Comando | O que faz |
|---|---|
| `uv run pytest` | Executa os testes |
| `uv run pytest --cov` | Executa os testes e exibe a cobertura de código, com as linhas não cobertas |
| `uv run pytest tests/api/health/test_health.py` | Executa apenas um arquivo de testes |
| `uv run pytest tests/unit` | Executa apenas os testes unitários |

Os testes de integração e de API sobem automaticamente um PostgreSQL descartável com [testcontainers](https://testcontainers.com/), por isso o **Docker precisa estar em execução**. O banco de desenvolvimento não é afetado. Os testes unitários não dependem do Docker.

### Organização dos testes

| Pasta | Tipo | O que testa |
|---|---|---|
| `tests/unit/` | Unitário | Regras de negócio isoladas, sem banco de dados nem HTTP |
| `tests/integration/` | Integração | Acesso a dados com PostgreSQL real |
| `tests/api/` | API | Endpoints, da requisição HTTP à resposta, passando pelas regras e pelo banco |

## Dependências

| Comando | O que faz |
|---|---|
| `uv add <pacote>` | Adiciona uma dependência de produção |
| `uv add --dev <pacote>` | Adiciona uma dependência de desenvolvimento |
| `uv sync --no-dev` | Instala apenas as dependências de produção |
