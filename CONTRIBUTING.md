# Contributing to memrail

Thanks for your interest in contributing. Here's how to get started.

## Setup

```bash
git clone https://github.com/bayurmdn/memrail
cd memrail
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

All tests must pass before submitting a PR. Tests must not make real LLM API calls — use mocks.

## File boundaries

| Directory | Rule |
|-----------|------|
| `memrail/core/` | Pure logic only — no I/O, no LLM calls except `compressor.py` |
| `memrail/cli/` | User-facing commands only |
| `memrail/integrations/` | Third-party adapter code only |
| `memrail/utils/` | Stateless helpers only |

## Key invariants

- **Never discard CRITICAL-tier content** — this is a hard contract
- **Summarization must be task-aware**, not blind truncation
- **Every pointer must be restorable** — if you store it, it must be retrievable
- **Token budget check runs before every model call**, not after

## Adding a new integration

1. Create `memrail/integrations/<name>.py`
2. Add a corresponding test in `tests/test_<name>.py`
3. Document it in `README.md` under a new section

## Adding benchmark tasks

Drop JSON files into `benchmarks/tasks/{coding,browser,research}/` following the schema in `task_001.json`.

## Code style

- Python 3.10+, type hints everywhere
- PEP 8, line length 100 (enforced by ruff)
- No magic numbers — use named constants

Run the linter before committing:

```bash
ruff check memrail/
```

## Pull requests

- Keep PRs focused — one feature or fix per PR
- Include tests for any new `core/` function
- Update `README.md` if you add user-facing behaviour
