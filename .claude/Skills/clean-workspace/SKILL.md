---
name: clean-workspace
description: Clean project workspace artifacts at one of three levels — safe (caches/temp only), extended (also build outputs), or deep (full reset, keeping source and git history). Use when the project has accumulated stale artifacts, disk space is tight, or a fresh build is needed. Triggers: "clean workspace", "clean project", "remove build artifacts", "fresh start", "clean up".
---

# Clean Workspace Skill

Removes accumulated project artifacts. Choose the level that matches your situation.

## Level 1 — Safe clean (default)

Removes only ephemeral cache and temp files. **No source code or build outputs touched.**

```powershell
# Python caches
Get-ChildItem -Recurse -Include "__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".ruff_cache", ".mypy_cache" |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# OS artifacts
Get-ChildItem -Recurse -Include "Thumbs.db", ".DS_Store", "desktop.ini" |
    Remove-Item -Force -ErrorAction SilentlyContinue
```

**POSIX equivalent:**
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -o -name "*.pyo" -delete 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null
```

## Level 2 — Extended clean

Also removes build outputs and generated files. **Leaves source, dependencies, and git history.**

```powershell
# Run Level 1 first
# Then:

# Python build outputs
Remove-Item -Recurse -Force dist, build, "*.egg-info", ".eggs" -ErrorAction SilentlyContinue

# Node build outputs
Remove-Item -Recurse -Force ".next", "out", "dist", ".turbo" -ErrorAction SilentlyContinue

# Coverage and test reports
Remove-Item -Recurse -Force htmlcov, ".coverage", "coverage.xml", "junit.xml" -ErrorAction SilentlyContinue
```

> Ask the user before running Level 2 if `dist/` or `build/` might contain files not tracked in git.

## Level 3 — Deep clean

**Full reset.** Removes dependencies, lock files, and all generated content.
Source code and git history are preserved. Use when environment is broken beyond repair.

```powershell
# Run Levels 1+2 first
# Then:

# Python virtual environment
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue

# Node modules
Remove-Item -Recurse -Force node_modules -ErrorAction SilentlyContinue

# ChromaDB and embedding model cache (will re-download on next use)
Remove-Item -Recurse -Force .memory\chroma_db\* -ErrorAction SilentlyContinue
Get-ChildItem .memory\models -Exclude .gitkeep | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
```

**After Level 3 — reinstall dependencies:**
```powershell
# Python:
uv sync --all-extras
# or: python -m venv .venv && pip install -r requirements.txt

# Node:
npm install
```

> **Never remove:** `.git/`, `.memory/`, `CLAUDE.md`, source code, `.env`.
> Check `.gitignore` — if a directory is gitignored it is safe to delete; if tracked it is not.

## Protected directories (never touch)

- `.git/` — git history
- `.memory/` — project memory bank (activeContext, lessons, etc.)
- `src/` or project source root — source code
- `.env` — secrets

## Post-clean verification

```powershell
python scripts/health_check.py
```

If health check fails after Level 3 — reinstall dependencies first, then re-run.
