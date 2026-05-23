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

## Release Workflow

Before any `release: vX.Y.Z` commit (i.e. any commit that bumps the `version`
field of `.claude-plugin/plugin.json`), every one of these must be true:

1. **`plugin.json::version`** = new `X.Y.Z`.
2. **`CHANGELOG.md`** — top header is `## [X.Y.Z]` (move from `[Unreleased]`).
3. **`task.md`** — every phase `[x]` (enforced by `check_task_guardrail.py`).
4. **`.memory/activeContext.md`** — every checkbox under any `## Sprint Goals`
   heading is `[x]`, or the section is removed entirely if the sprint is closed
   (enforced by `check_activectx_sprint_goals.py`, fires on plugin.json version
   bump).
5. **Tag** — annotated `git tag -a vX.Y.Z -m "..."`, pushed via `git push --tags`.
   The pre-push `.githooks/pre-push` shim re-verifies (1) and (2) against the
   tag suffix.

The activeContext rule promoted from a lesson (v2.1.1 + v2.2.0 audits both
caught `[ ]` Sprint Goals checkboxes surviving past a release commit) into a
deterministic pre-commit hook in v2.3 Phase 1. Don't try to bypass it — the
fix is mechanical: mark the phase `[x]`, re-stage, retry.

Don't plan the *next* sprint in the same commit that closes the current one.
Open a new commit (`chore(sprint): start v(X.Y+1)`) for next-sprint Sprint
Goals — otherwise the new section's `[ ]` checkboxes will trip the guardrail.
