# Copilot Repository Instructions

## Project

This is a small educational FastAPI Task Management API used to demonstrate GitHub Copilot Ask, Edit and Agent modes.

## Stack

- Python 3.11+
- FastAPI
- Pydantic
- pytest

## Structure

- `app/api/` — HTTP routes
- `app/services/` — business logic
- `app/repositories/` — in-memory data access
- `app/models/` — domain models
- `app/schemas/` — API request/response models
- `tests/` — automated tests

## Architecture

Use:

API → Service → Repository

Do not put business logic directly in route handlers.

## Coding conventions

- Use type hints.
- Prefer small, readable functions.
- Reuse existing patterns.
- Keep changes minimal.
- Do not add dependencies unnecessarily.
- Do not modify unrelated files.

## Testing

Use pytest.

A task is complete only when:
- implementation is complete
- relevant tests exist
- tests pass
- final diff is focused

## Demo behavior

This repository intentionally contains TODOs. Do not remove TODOs or redesign the project unless explicitly requested.

When implementing a feature:
1. Inspect existing code and tests.
2. Explain the plan for non-trivial work.
3. Implement the smallest reasonable change.
4. Run tests.
5. Fix failures caused by the change.
6. Summarize files changed and verification results.
