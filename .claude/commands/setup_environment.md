---
description: Set up the project environment from scratch on a new machine
model: sonnet
---

# Environment Setup

> **Goal:** Get a clean machine to a fully working project environment in one pass.
> **OS:** Windows 11 (primary). **IDE:** Claude Code.
> Fill in stack-specific sections based on your project's `.ecosystem.toml`.

## Step 1: System dependencies

| Tool | Check | Install |
|---|---|---|
| Git | `git --version` | https://git-scm.com/download/win |
| Python 3.11+ | `python --version` | https://www.python.org/downloads/ (check "Add to PATH") |
| Node.js LTS | `node --version` | https://nodejs.org/ |
| Claude Code | in PATH | https://docs.anthropic.com/en/claude-code |

Optional package managers (install the one matching your stack):

| Tool | Check | Install |
|---|---|---|
| uv (Python) | `uv --version` | PowerShell: `irm https://astral.sh/uv/install.ps1 \| iex` |
| pnpm (Node) | `pnpm --version` | `npm install -g pnpm` |

## Step 2: Clone and install dependencies

```powershell
git clone <repo-url> C:\${PROJECT_NAME}
cd C:\${PROJECT_NAME}
```

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

## Step 3: Pre-commit hooks

```powershell
# Python projects with uv:
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
# Python projects with pip:
pre-commit install
pre-commit install --hook-type pre-push
# Node projects:
npx husky install
```

This activates:
- Linter enforcement (ruff / eslint)
- `task.md` guardrail (blocks commit when tasks are unchecked)
- Dependency sync check
- **Pre-push:** version-sync guardrail (blocks `git push --tags` when
  `plugin.json`, CHANGELOG, `.ecosystem.toml` and the pushed tag disagree)

## Step 4: Health check

```powershell
python scripts/health_check.py
```

Expected: all checks pass. If any fail — read the output and fix before proceeding.

## Step 5: Configure MCP servers for Claude Code

### 5.1 Secrets (`.env`)

```powershell
Copy-Item .env.example .env
# Open .env and fill in GITHUB_PERSONAL_ACCESS_TOKEN
```

Create GitHub token: https://github.com/settings/tokens (scopes: `repo`, `read:org`).

### 5.2 MCP server install

```powershell
.\scripts\setup_mcp.ps1
```

This installs the minimal MCP servers declared in `.mcp.json`. Node-based servers
(`sequential-thinking`, `github`) run via `npx` on first use — no manual install needed.

### 5.3 Verify MCP

Restart Claude Code and run `/mcp` — both servers should appear green:
- `sequential-thinking` ✅
- `github` ✅

If any are red — check `%USERPROFILE%\.claude\logs\` or run the server command manually
for diagnostics.

### 5.4 Custom skills

Project skills live in `.claude/skills/` and are picked up by Claude Code automatically.
Run `/skills` in Claude Code to verify they appear.

## Step 6: First run

Run whatever your project's entry point is (see `build_command` in `.ecosystem.toml`).
Verify it starts without errors.

---

## Readiness checklist

- [ ] Git, Python, Node.js installed
- [ ] Dependencies installed (`uv sync` / `npm install`)
- [ ] Pre-commit hooks installed
- [ ] `python scripts/health_check.py` passes
- [ ] `.env` filled (GitHub PAT at minimum)
- [ ] `.\scripts\setup_mcp.ps1` ran successfully
- [ ] Claude Code `/mcp` shows both servers green
- [ ] Project entry point launches

---

## Ecosystem configuration snapshot

| Component | Count | Notes |
|---|---|---|
| Memory Bank (`.memory/`) | 6 files | activeContext, lessons, progress, brief, patterns, tech |
| Slash commands (`.claude/commands/`) | 7 | new_session, audit, extract_lesson, create_spec, tdd, commit, setup |
| Modular rules (`.agents/rules/`) | 3 | common, git, code-quality |
| Skills (`.claude/skills/`) | 2 | clean-workspace, deploy-fresh |
| MCP servers | 2 minimum | sequential-thinking, github |
| Context model | Progressive Disclosure | 🔴/🟡/🟢 tiers |
| IDE | Claude Code (Anthropic) | |
