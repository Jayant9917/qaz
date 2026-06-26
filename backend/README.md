# NOVO Backend

FastAPI modular-monolith foundation for NOVO.

## Local commands

From backend:

- Install: python -m pip install -e ".[dev]"
- Run: python -m uvicorn novo.main:app --reload --app-dir src
- Test: python -m pytest
- Lint: python -m ruff check .
- Format: python -m ruff format .
- Types: python -m mypy src tests
- Migrate: python -m alembic upgrade head

Copy the repository .env.example to .env before connecting infrastructure.

Infrastructure readiness is optional in development and required in production.
