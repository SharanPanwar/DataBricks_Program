# Expected Final State

After the demo tasks are completed:

## Task creation

`POST /tasks`

Input:

```json
{"title": "  Learn Copilot  "}
```

Expected:
- HTTP 201
- title becomes `Learn Copilot`
- new ID is assigned

## Task deletion

`DELETE /tasks/{task_id}`

Existing task:
- HTTP 204
- task is removed

Missing task:
- HTTP 404
- detail is `Task not found`

## Verification

```bash
pytest -q
```

All tests should pass after the TODOs are completed.
