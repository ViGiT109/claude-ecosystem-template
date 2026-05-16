# Code Standards and Conventions (Extended Reference)

> **Full standards for the AI assistant.**

## 1. Architecture

### Project structure

- Organize code into modules and packages that reflect domain concepts.
- Prefer flat structures for small projects; introduce packages only when a directory
  would exceed ~10 modules.
- Imports: absolute from the project root (e.g. `from config import settings`).
- Record significant structural decisions in `docs/adr/`.

### Adding a new module

1. Create the file in the appropriate location.
2. Add to linter's known-first-party list (ruff `isort.known-first-party`).
3. Add to `README.md` module table.
4. Update `.memory/activeContext.md` (add module to current focus).
5. Update `pyproject.toml` or `package.json` if new dependencies are required.

## 2. Logging

### Rule

```python
# ✅ Correct (backend modules)
from logger import get_logger
logger = get_logger(__name__)
logger.info("Loaded %d records", count)

# ❌ Forbidden (backend modules)
print(f"Loaded {count} records")
```

### Exceptions

- CLI entry points (`main.py`) — `print()` allowed for user-facing output.
- UI/GUI modules — `print()` allowed where stdout redirection is intentional.

## 4. Type hints

```python
# ✅ Correct (Python 3.11+ style)
def build_dataset(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame: ...
def get_config(key: str, default: int | None = None) -> int | None: ...

# ❌ Incorrect
def build_dataset(df, columns): ...          # Missing types
from typing import Optional, List           # Outdated style (pre-3.10)
```

## 5. Docstrings (Google Style)

```python
def process_records(
    records: list[dict],
    batch_size: int,
) -> list[dict]:
    """Process records in batches.

    Args:
        records: Input records to process.
        batch_size: Number of records per batch.

    Returns:
        List of processed records.

    Raises:
        ValueError: If records is empty.
    """
```

Short functions (≤ 5 lines, self-evident purpose) do not need a docstring.

## 7. Git conventions

See `.agents/rules/git.md` for full Conventional Commits rules.

Quick reference:
- `feat(scope): description` — new feature
- `fix(scope): description` — bug fix
- `refactor(scope): description` — no behavior change
- `docs(scope): description` — documentation

## 9. Benchmarking

When refactoring performance-critical code — measure before and after:

```bash
python benchmarks.py   # or your project's benchmark command
```

Record results in `BENCHMARKS.md` if the project tracks them.
Do not assume a refactor is faster — measure it.

## 10. Testing

- Unit tests: `pytest` in `tests/`
- Run with: `pytest tests/ -v`
- Smoke-test new features before marking the task complete
- Integration tests should use real external services when possible (or recorded fixtures);
  avoid mocks for critical data paths
- Coverage is a guide, not a target — test behaviors, not lines
