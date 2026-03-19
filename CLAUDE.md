# CLAUDE.md - Project Instructions for loadtest-api-bench

## Project Overview

Load testing API backend built with FastAPI. Compares Cloud SQL / Spanner / BigQuery response characteristics on Cloud Run using Locust.

## Key Decisions (Already Finalized)

These decisions have been made and MUST be followed:

1. **Framework**: FastAPI
2. **ORM**: SQLAlchemy 2.0
3. **PK**: UUID (all DBs unified, for Spanner compatibility)
4. **Class Design**: Template Method pattern (案C) — see `docs/ARCHITECTURE.md`
5. **async/sync**: async interface unified. Cloud SQL/SQLite use native async, Spanner/BigQuery wrap sync via `asyncio.to_thread()`
6. **openapi-generator**: api.yaml is Single Source of Truth. Generated code goes to `output/`, hand-written code in `src/loadtest_api/`. Regenerate on api.yaml changes.
7. **Testing**: TDD (t-wada style Red-Green-Refactor). Unit tests only for now (SQLite in-memory). Integration tests added later.
8. **DI**:
   - Logging: structured JSON on Cloud Run, human-readable locally
   - DB: SQLite for tests, real DBs for production
9. **DB operations**: Read-only (no writes)
10. **Seed data**: ~100,000 records
11. **Repository**: `loadtest-api-bench` (public on GitHub)

## Project Structure

```
loadtest-api-bench/
├── api.yaml                    # OpenAPI spec (Single Source of Truth)
├── pyproject.toml              # Rye project config
├── Dockerfile
├── output/                     # openapi-generator output (do not hand-edit)
├── src/
│   └── loadtest_api/
│       ├── __init__.py
│       ├── main.py             # FastAPI app
│       ├── config.py           # pydantic-settings
│       ├── dependencies.py     # DI providers
│       ├── logging.py          # Log format factory
│       ├── models/
│       │   └── user.py         # SQLAlchemy ORM + Pydantic schemas
│       ├── api/
│       │   └── users.py        # Route handlers
│       └── repositories/
│           ├── base.py         # DBAccessor (ABC)
│           ├── async_accessor.py  # AsyncDBAccessor
│           ├── sync_accessor.py   # SyncDBAccessor
│           ├── sqlite.py       # SQLiteAccessor
│           ├── cloud_sql.py    # CloudSQLAccessor
│           ├── spanner.py      # SpannerAccessor
│           └── bigquery.py     # BigQueryAccessor
├── tests/
│   ├── conftest.py             # SQLite in-memory fixture
│   ├── test_repositories.py    # Repository unit tests
│   └── test_api_users.py       # API endpoint tests
└── (Locust scenarios are in a separate repository)
```

## Development Commands

```bash
rye run pytest tests/ -v        # Run tests
```

## Implementation Order

1. Rye project init + api.yaml creation
2. openapi-generator code generation
3. DI foundation (config, logging, repository protocol)
4. TDD: SQLite Repository → API endpoints
5. Cloud SQL / Spanner / BigQuery Repositories
6. Dockerfile + Cloud Run config
7. Locustfile → **別リポジトリで管理予定**

## Test Naming Convention

Use Japanese for test method names:
```python
def test_ユーザーIDで1件取得できる():
    ...
```

## Architecture Reference

See `docs/ARCHITECTURE.md` for full class design details, code examples, and rationale.
