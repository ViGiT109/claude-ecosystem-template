# Environment Setup — ${PROJECT_NAME}

> **Goal:** Get a new machine to a fully working development environment.
> **Primary OS:** Windows 11. **IDE:** Claude Code.
> Stack-specific sections are gated by your project's language (see `.ecosystem.toml`).

---

## Step 1: System tools

Install these once per machine:

| Tool | Version check | Install |
|---|---|---|
| Git | `git --version` | https://git-scm.com/download/win |
| Claude Code | `claude --version` | https://docs.anthropic.com/en/claude-code |
| Node.js LTS | `node --version` | https://nodejs.org/ |

**Python projects:**

| Tool | Version check | Install |
|---|---|---|
| Python 3.11+ | `python --version` | https://www.python.org/downloads/ (check "Add to PATH") |
| uv (recommended) | `uv --version` | PowerShell: `irm https://astral.sh/uv/install.ps1 \| iex` |

**Node projects:**

| Tool | Version check | Install |
|---|---|---|
| pnpm (optional) | `pnpm --version` | `npm install -g pnpm` |

---

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

---

## Step 3: Configure secrets

```powershell
Copy-Item .env.example .env
# Open .env and fill in:
# GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...
```

Create a GitHub token at https://github.com/settings/tokens
Required scopes: `repo`, `read:org`.

---

## Step 4: Pre-commit hooks

```powershell
# Python (uv):
uv run pre-commit install
# Python (pip):
pre-commit install

# Always: activate the raw .githooks/pre-push shim for the version-sync guardrail.
git config core.hooksPath .githooks
```

Hooks enabled by default:
- **Ruff lint** — Python projects only
- **task.md guardrail** — blocks commit when unchecked tasks remain
- **deps-sync** — verifies `uv.lock` is in sync with `pyproject.toml`
- **Pre-push: version-sync** (via `.githooks/pre-push` shim) — blocks
  `git push --tags` when `plugin.json`, CHANGELOG and the pushed tag
  disagree. Delegates remaining pre-push hooks back to pre-commit.

---

## Step 5: MCP server setup

```powershell
.\scripts\setup_mcp.ps1
```

This installs the MCP servers declared in `.mcp.json`:
- `sequential-thinking` — auto-installed via `npx` on first use
- `github` — auto-installed via `npx` on first use

Restart Claude Code after running setup. Verify with `/mcp` — both servers should be green.

---

## Step 6: Health check

```powershell
python scripts/health_check.py
```

All checks must pass. If any fail — read the output and fix before proceeding.

---

## Step 7: First Claude Code session

1. Open Claude Code in the project folder.
2. Run `/new_session` — should inject context from `activeContext.md`, lessons, and git status.
3. Run `/setup_environment` for interactive guided setup.

---

## Readiness checklist

- [ ] Git, Python, Node.js installed
- [ ] Dependencies installed (`uv sync` / `npm install`)
- [ ] `.env` filled (GitHub PAT)
- [ ] Pre-commit hooks installed
- [ ] `python scripts/health_check.py` passes
- [ ] `.\scripts\setup_mcp.ps1` ran successfully
- [ ] Claude Code `/mcp` shows both servers green
- [ ] `/new_session` loads without errors

---

## Current ecosystem configuration

| Component | Count | Notes |
|---|---|---|
| Memory Bank (`.memory/`) | 7 files | activeContext, lessons, progress, brief, patterns, tech, cc_state |
| Slash commands (`.claude/commands/`) | 7 | new_session, audit, extract_lesson, create_spec, tdd, commit, setup |
| Modular rules (`.agents/rules/`) | 3 | common, git, code-quality |
| Skills (`.claude/skills/`) | 2 | clean-workspace, deploy-fresh |
| MCP servers | 2 minimum | sequential-thinking, github |
| Context model | Progressive Disclosure | 🔴/🟡/🟢 tiers |
| IDE | Claude Code (Anthropic) | claude-opus-4-7 / claude-sonnet-4-6 |
