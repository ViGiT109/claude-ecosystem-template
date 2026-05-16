# Git Rules

> Git conventions, commit messages, and workflow for this project.

## Conventional Commits

Format: `type(scope): message`

### Types

| Type | When to use |
|---|---|
| `feat` | New functionality |
| `fix` | Bug fix |
| `refactor` | Refactoring without behavior change |
| `docs` | Documentation only |
| `test` | Tests only |
| `chore` | Maintenance (deps, configs, tooling) |
| `perf` | Performance improvement |
| `style` | Formatting, no logic change |

### Scopes

Defined in `.ecosystem.toml` under `[git] scopes`. Defaults: `core`, `api`, `ui`, `config`, `docs`, `infra`.
Update after running `bootstrap.ps1` for project-specific scopes.

## What NOT to commit

- `.env` — secrets
- `.venv/`, `venv/`, `node_modules/` — local environments
- `__pycache__/`, `*.pyc` — Python caches
- `.claude/settings.local.json` — personal Claude Code settings
- `.memory/chroma_db/`, `.memory/models/` — generated vector stores
- Large data files (add project-specific patterns to `.gitignore`)

## Mandatory push

**ALWAYS** run `git push` after committing. Do not leave local-only commits.

## Branch naming

- `main` — stable branch (default)
- `feat/<name>` — new features
- `fix/<name>` — bug fixes
- `refactor/<name>` — module refactoring
- `chore/<name>` — maintenance

## Session finalization

Close every session via `/commit_and_release`:
1. Health check (`python scripts/health_check.py`)
2. task.md guardrail check
3. `git add` + `git commit` (Conventional Commits format)
4. `git push origin main`

## Versioning

- Semantic Versioning: `MAJOR.MINOR.PATCH`
- Tags: `git tag -a v0.X.Y -m "Release description"`
- Update `CHANGELOG.md` before every tag (move `[Unreleased]` → `[X.Y.Z]`)
