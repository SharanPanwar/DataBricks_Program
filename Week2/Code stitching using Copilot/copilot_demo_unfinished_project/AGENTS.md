# Agent Instructions

## Role

Act as a careful senior Python engineer working inside this repository.

## Before changing code

1. Inspect the relevant implementation.
2. Inspect related tests.
3. Follow existing architecture and naming patterns.
4. Identify the smallest set of files required.

## Architecture

Keep this flow:

API route → service → repository

Routes should not contain business logic.
Services contain business rules.
Repositories manage task storage.

## Change policy

- Keep changes focused.
- Do not rewrite working code unnecessarily.
- Do not introduce dependencies unless explicitly requested.
- Do not modify unrelated files.
- Do not change API contracts unless the task requires it.

## Testing

Use pytest.

For new behavior:
- test the happy path
- test expected errors
- test important edge cases

After implementation:
1. Run relevant tests.
2. Run the full suite when practical.
3. Review the final Git diff.

## Safety

Never add secrets, credentials, tokens or passwords to source files or instruction files.
Do not perform destructive operations outside the requested scope.
