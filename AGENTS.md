# AGENTS.md

Logos is an MVP for a logistics incident response center: drivers report road incidents, analysts and supervisors triage and resolve them. Code quality, a clean commit history and documented decisions matter as much as features.

## Where things are

- `docs/desafio.md`: the original product brief (source of truth for scope).
- `docs/requisitos.md`: personas, business rules (`RN-xx`), user stories (`US-xx`) and non-functional requirements (`RNF-xx`).
- `docs/adr/`: architecture decision records (`ADR-xx`). Read the relevant ADR before changing a decision it covers.
- `backend/`: Python API (FastAPI). See `backend/README.md` for every command.
- Frontend (React) does not exist yet.

## Commands

Run from `backend/` unless noted. The integration and API tests start a disposable PostgreSQL with testcontainers, so Docker must be running.

```bash
docker compose up -d db                  # from repo root: local PostgreSQL
uv sync                                  # install dependencies
uv run uvicorn app.main:app --reload     # API at http://localhost:8000/api/docs
uv run pytest                            # all tests
uv run pytest tests/unit                 # unit tests only (no Docker)
uv run ruff check . && uv run ruff format --check . && uv run mypy app tests migrations scripts
uv run alembic revision --autogenerate -m "description"   # then review the generated file
uv run alembic upgrade head
```

A change is done only when tests, ruff and mypy (strict) all pass.

## Backend architecture

Code is organized by feature module, not by technical layer:

```
app/
├── main.py          # create_app()
├── router.py        # includes every module router under /api
├── shared/          # config, db (Base, session, constraints), domain errors
└── modules/<name>/  # files as needed: enums, models, repository, service, router, schemas
```

- Modules may import from `shared` and from other modules; `shared` never imports from a module.
- **Business rules live only in `service.py`.** Models describe data; enums hold values and intrinsic properties (e.g. `Criticality.priority`).
- **Permissions (ADR-06):** a rule that depends only on the role goes on the route with `require_role(...)`; a rule that depends on the data (e.g. assignee, reporter) stays in the service, which receives the `CurrentUser`. Never check the same rule in both layers.
- **Repositories only access data.** They are declared as a `Protocol` and implemented with SQLAlchemy; services depend on the protocol.
- The database only enforces value validity through `enum_check` (enums are `native_enum=False` VARCHAR columns). Do not add CHECK constraints for business rules.
- Services raise `app.shared.errors` (`NotFoundError`, `PermissionDeniedError`, `BusinessRuleError`, `ConflictError`), which the API layer must map to 404/403/422/409. Their messages are shown to end users, so they are written in Portuguese and without technical terms.
- Every write to an incident goes through `update_if_version` (optimistic locking, ADR-02). Never update an incident without checking the version.
- New tables must be imported in `migrations/env.py`, otherwise autogenerate ignores them.
- SQLAlchemy is synchronous; one transaction per request via `get_session`.
- API responses use Pydantic schemas, never ORM objects (they would leak fields such as `password_hash`).

## Tests

- `tests/unit/`: services with `tests/fakes.py` (in-memory repositories). No database.
- `tests/integration/`: repositories, migrations and concurrency against real PostgreSQL.
- `tests/api/`: endpoints through `TestClient` (`client` without database, `db_client` with it).
- Use `tests/factories.py`: `build_*` for in-memory objects, `create_*` to persist them.
- Each test runs inside a transaction that is rolled back; tests that need committed data (e.g. concurrency) must clean up after themselves.
- Expected values in tests are written independently from the implementation (e.g. the expected transition table), never imported from it.

## Conventions

- Code identifiers, comments and docstrings in English. Documentation in `docs/` and READMEs in Portuguese.
- Keep comments minimal: explain why, not what.
- Commits are small and focused, using Conventional Commits in English (`feat(backend): ...`, `test(backend): ...`, `build: ...`, `docs: ...`).
- Business rules in `docs/requisitos.md` describe observable behavior only; implementation choices go into ADRs.
- Prefer the simplest solution that meets the requirement; do not create empty files or abstractions ahead of need.
