---
name: deploy-fresh
description: Set up a fresh project environment on a new machine or after a deep clean — install dependencies, configure environment, run health check, verify MCP servers. Use when onboarding a new developer, recovering from environment corruption, or provisioning a CI runner. Triggers: "deploy fresh", "fresh install", "setup from scratch", "new machine setup", "reinstall everything".
---

# Deploy Fresh Skill

Reproducible environment setup from a clean state. Assumes git is installed and the
repo has already been cloned. For full OS-level setup see `ENVIRONMENT_SETUP.md`.

## Step 1: Read project configuration

```powershell
# Check what stack this project uses
Get-Content .ecosystem.toml
```

Proceed to the relevant language section below. If language is not set — ask the user.

## Step 2: Install dependencies

**Python (uv):**
```powershell
uv sync --all-extras
```

**Python (pip):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Node:**
```powershell
npm install
```

**Both (monorepo):**
```powershell
uv sync --all-extras
npm install
```

## Step 3: Configure environment

```powershell
# Create .env from template (if not already present)
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env — fill in your tokens before proceeding."
}
```

Open `.env` and set at minimum:
- `GITHUB_PERSONAL_ACCESS_TOKEN` — required for the github MCP server

## Step 4: Install pre-commit hooks

```powershell
# Python:
uv run pre-commit install
# or: pre-commit install

# Node (if husky configured):
npx husky install

# Always: activate the raw .githooks/pre-push shim
git config core.hooksPath .githooks
```

`git config core.hooksPath .githooks` wires the version-sync guardrail
(`scripts/check_version_sync.py` via `.githooks/pre-push`) — blocks
`git push --tags` when `plugin.json`, CHANGELOG and the pushed tag
disagree. v2.2.1 moved the guardrail out of pre-commit framework
because the framework was silently skipping it on Windows.

## Step 5: Run health check

```powershell
python scripts/health_check.py
```

All checks must pass before continuing. Common failures after a fresh install:
- Missing `.env` values — fill them in and re-run
- Wrong Python version — check `.ecosystem.toml` or `pyproject.toml` for minimum version
- Missing system tool — install it and re-run

## Step 6: Install MCP servers

```powershell
.\scripts\setup_mcp.ps1
```

## Step 7: Verify in Claude Code

1. Restart Claude Code in the project directory.
2. Run `/mcp` — both `sequential-thinking` and `github` should be green.
3. Run `/new_session` — should load `activeContext.md`, lessons, and git status.
4. Run a quick sanity test: make a trivial edit and `git commit` — pre-commit hooks should fire.

## Post-setup checklist

- [ ] `.ecosystem.toml` present and filled
- [ ] Dependencies installed without errors
- [ ] `.env` filled (at minimum: `GITHUB_PERSONAL_ACCESS_TOKEN`)
- [ ] Pre-commit hooks active (`git commit` triggers them)
- [ ] `python scripts/health_check.py` passes
- [ ] Claude Code `/mcp` shows both servers green
- [ ] `/new_session` loads correctly

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `python` not found | PATH not set | Re-install Python with "Add to PATH" checked |
| `uv` not found | uv not installed | `irm https://astral.sh/uv/install.ps1 \| iex` then restart terminal |
| MCP server red | Missing token or wrong path | Check `.env` and `.mcp.json` |
| `health_check.py` fails | Dependency mismatch | `uv sync` or `pip install -r requirements.txt` again |
| `pre-commit` not found | hooks not installed | `uv run pre-commit install` |
