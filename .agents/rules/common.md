# Common Rules

> Universal rules for the AI assistant, applicable to any module in this project.

## Logging

```python
from logger import get_logger
logger = get_logger(__name__)
# FORBIDDEN: print() in backend modules
# ALLOWED: print() only in CLI entry points (e.g. main.py) and UI modules
```

The list of backend modules where `print()` is forbidden is declared in `.ecosystem.toml`
under `[project.python] backend_modules`. The pre-commit hook and `health_check.py` enforce this.

## Type hints

- Type hints on **all** public methods (Python 3.11+: `list[str]`, `int | None`)
- Google Style docstrings
- New files must have type hints (enforced by ruff ANN rules)
- Existing code: gradual migration acceptable (use per-file-ignores in pyproject.toml)
- `self`/`cls` are not annotated (ruff ANN does not require them by default)

## File I/O discipline

- **Never read large runtime files in full** (logs, audit trails, JSONL databases).
  Always use tail/head equivalents:
  ```powershell
  Get-Content -Tail 200 path/to/large.log
  ```
  ```bash
  tail -200 path/to/large.log
  ```
- If a file could grow unboundedly at runtime — read only the last N lines.

## Dependencies

- Source of truth: `pyproject.toml` (+ `uv.lock` if using uv)
- Add packages: `uv add <package>` (or `pip install <package>` + update requirements)
- Sync: `uv sync` (or `pip install -r requirements.txt`)
- Do not commit lock file conflicts unresolved

## PowerShell CLI

- **AVOID** inline Python via `python -c "..."` in PowerShell — shell escaping breaks
  quotes and special characters. Instead: write a `.py` file in `scratch/` and run it.
- PowerShell does not support `&&` chaining — use `;` or separate commands.
- When quoting paths in PowerShell: prefer `"double quotes"`, not backtick escaping.

## API Inspection

- Before calling any internal function — **verify the signature** via `Read` or `Grep`.
- Pay special attention to: optional kwargs, default values, argument order.
- Do not guess parameters — read the code.
