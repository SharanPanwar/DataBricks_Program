# Copilot Demo — Unfinished Task Management API

This is an intentionally **unfinished FastAPI project** for demonstrating GitHub Copilot Ask, Edit, and Agent modes.

## Demo goals

1. **Ask mode** — understand the repository and TODOs.
2. **Edit mode** — complete a small function.
3. **Agent mode** — implement a multi-file feature, run tests, and fix failures.
4. Review the Git diff.
5. Run the complete test suite.

## Stack

- Python 3.11+
- FastAPI
- Pydantic
- pytest
- In-memory repository

## Setup

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Install:
```bash
pip install -r requirements.txt
```

Run:
```bash
uvicorn app.main:app --reload
```

Docs:
```text
http://127.0.0.1:8000/docs
```

Tests:
```bash
pytest -q
```

## Suggested demo

### 1. Ask mode

```text
Analyze this repository as if you are onboarding to an existing FastAPI project.

Do not modify anything.

Explain:
1. The folder structure.
2. The API → service → repository architecture.
3. All TODOs.
4. Which TODO is safest for an Edit-mode demonstration.
5. Which TODO is appropriate for an Agent-mode demonstration.
6. What the tests expect.
```

### 2. Edit mode

Open `app/services/task_service.py` and select `validate_title()`.

```text
Implement only validate_title().

Requirements:
- Strip leading and trailing whitespace.
- Reject an empty result.
- Raise ValueError("Task title cannot be empty").
- Do not modify unrelated files.
- Follow the existing project style.
```

Then:
```bash
pytest -q tests/test_task_service.py
```

### 3. Agent mode

```text
Implement task deletion.

Before changing anything:
1. Inspect the repository and tests.
2. Identify the route, service and repository changes required.
3. Follow the existing API → service → repository architecture.

Then implement:
- DELETE /tasks/{task_id}
- repository deletion
- service delegation
- 204 when deletion succeeds
- 404 with "Task not found" when the task does not exist

Add or update tests for success and not-found behavior.

Constraints:
- No new dependencies.
- No database changes.
- No unrelated file changes.

Run the relevant tests and fix failures caused by your changes.
At the end, summarize files changed and test results.
```

### 4. Review

```text
Review the current changes as a senior Python engineer.

Do not modify anything yet.

Check:
- correctness
- edge cases
- API behavior
- architecture consistency
- test coverage
- unnecessary changes
- maintainability

Report findings first.
```

Finally:
```bash
git status
git diff
pytest -q
```

**Important:** This repository is intentionally incomplete. Do not treat it as production-ready before the TODOs are completed and tests pass.
