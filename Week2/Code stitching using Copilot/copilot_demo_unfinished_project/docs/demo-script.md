# Live Demo Script

## Opening

> This is a deliberately unfinished FastAPI project. I will use Copilot Ask, Edit and Agent modes to finish it while keeping the developer in control.

## Step 1 — Ask mode

Prompt:

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

Teaching point:

> Ask mode is for understanding, investigation and planning without changing the project.

## Step 2 — Edit mode

Open `app/services/task_service.py` and select `validate_title()`.

Prompt:

```text
Implement only validate_title().

Requirements:
- Strip leading and trailing whitespace.
- Reject an empty result.
- Raise ValueError("Task title cannot be empty").
- Do not modify unrelated files.
- Follow the existing project style.
```

Run:

```bash
pytest -q tests/test_task_service.py
```

Teaching point:

> Edit mode is best for small, controlled changes.

## Step 3 — Agent mode

Prompt:

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

Teaching point:

> Agent mode is useful when a task requires repository exploration, multiple file changes, commands and iteration.

## Step 4 — Review

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

## Step 5 — Git review

```bash
git status
git diff
pytest -q
```

Explain:

> The AI summary is not the source of truth. The actual diff and test results are.

## Final lesson

```text
ASK
  ↓
UNDERSTAND
  ↓
PLAN
  ↓
EDIT / AGENT
  ↓
TEST
  ↓
REVIEW DIFF
  ↓
VERIFY
```
