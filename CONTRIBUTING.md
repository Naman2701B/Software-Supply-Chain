# Contributing

Thanks for helping improve this project. This guide covers how to report issues,
submit changes, and what every pull request must pass.

## Reporting issues

- Search existing issues first to avoid duplicates.
- For a bug, include the command you ran, the full output, and your Python version.
- When an issue is about specific code, link the line: click the line number on
  GitHub and choose **Reference in new issue**.
- Security problems go through [SECURITY.md](SECURITY.md), not public issues.

## Submitting pull requests

`main` is protected: all changes go through a pull request, and history is kept
linear (no merge commits).

1. Create a branch from `main` (e.g. `fix/empty-api-response`).
2. Make your change, with tests.
3. Run the checks below and make sure they all pass.
4. Open a PR that explains what changed and why, and link the issue it resolves
   (e.g. `Fixes #12`).
5. Address review comments, then rebase onto `main` if it has moved on.

## Development setup

```bash
poetry install
pre-commit install
```

## Coding style

- Format with `ruff format .` (PEP 8, 88-character lines, double quotes).
- Lint with `ruff check .`; it must report 0 errors.
- Type hints are required: `mypy main.py merkle_proof.py util.py` runs in strict
  mode and must pass.
- `bandit -r .` must report no issues.
- Keep functions small and focused, and prefer raising a clear `ValueError` over
  letting an unexpected `KeyError` or `StopIteration` escape.

## Testing requirements

- Tests live in `tests/` and run with `poetry run pytest`.
- Every bug fix or feature needs a test.
- Tests must not call the network; mock `requests.get` and use the recorded
  fixtures in `tests/data/`.
- Total coverage must stay at or above 75% (the test run fails otherwise).

## Secrets

Never commit tokens, keys or credentials. The TruffleHog pre-commit hook blocks
commits containing secrets; do not bypass it with `--no-verify`.
