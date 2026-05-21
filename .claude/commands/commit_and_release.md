---
description: Commit changes and (optionally) create a new release tag
model: sonnet
---

# Commit and Release

Clean commit workflow with quality checks before pushing.

1. Run linter (if configured for this project's stack):
```powershell
# Python projects:
python -m ruff check . --config pyproject.toml
# Node projects:
npm run lint
# Other: run your stack's lint command
```

2. Run health check:
```powershell
python scripts/health_check.py
```

3. Verify `CHANGELOG.md` is updated:
```
Read the [Unreleased] section in CHANGELOG.md — it must describe the current changes.
If empty — update CHANGELOG.md first.
```

4. Check git status:
```bash
git status --short
```

5. Stage files and commit:
```bash
git add -A
```
```bash
git commit -m "type(scope): description of change"
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`
Scopes: `${PROJECT_SCOPES}` (set in `.ecosystem.toml` — defaults: `core`, `api`, `ui`, `config`, `docs`, `infra`)

6. **MANDATORY — push to remote:**
```bash
git push origin main
```

7. (Optional) Create a release tag:
```bash
git tag -a v0.X.Y -m "v0.X.Y: Release description"
git push --tags
```
When tagging — move entries from `[Unreleased]` into a new `[0.X.Y]` section in `CHANGELOG.md`.
