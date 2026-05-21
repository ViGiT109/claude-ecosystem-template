---
name: initialize_project
description: Full project initialization and ecosystem readiness check. Triggers on "инициализация экосистемы", "initialize ecosystem", "ecosystem init", "init project", "setup project", "первый запуск".
model: opus
---

You are running the **ecosystem initialization** workflow. Complete all phases in order without stopping for confirmation unless a critical ambiguity requires it.

---

## Phase 1 — Detect state

Read `.ecosystem.toml` and `CLAUDE.md`:

```bash
# Check for unsubstituted placeholders
grep -r '\${PROJECT_NAME}' CLAUDE.md README.md .memory/projectbrief.md 2>/dev/null | head -5
```

- If `${PROJECT_NAME}` **not found** anywhere → project is already initialized. Skip to Phase 4 (readiness check only).
- If `${PROJECT_NAME}` **found** → proceed with full initialization.

---

## Phase 2 — Collect project info

Ask the user these questions **in a single message** (number them, expect answers in one reply):

```
To initialize this project I need a few details:

1. **Project name** (slug, e.g. `yandex-direct-bot`, `my-api`)
2. **One-sentence vision** — what problem does it solve?
3. **Primary stakeholders / users** (e.g. "solo developer", "internal team")
4. **Language / stack**: python | node | both | other
5. **Entry point** (e.g. `main.py`, `src/index.ts`) — or leave blank
6. **Build/run command** (e.g. `python main.py`, `npm start`) — or leave blank
7. **Conventional Commit scopes**, comma-separated  
   Default: `core,api,ui,config,docs,infra`
```

Wait for the user's answers, then proceed.

---

## Phase 3 — Apply initialization

### 3a. Write `.ecosystem.toml`

Determine `package_manager`:
- Python: default `uv` unless user specified otherwise
- Node: default `npm`

Write the file:

```toml
[project]
name = "<PROJECT_NAME>"
language = "<LANGUAGE>"
entry_module = "<ENTRY_MODULE>"
build_command = "<BUILD_COMMAND>"

[project.python]
backend_modules = []
min_version = "3.11"
package_manager = "<PYTHON_PM>"

[project.node]
package_manager = "<NODE_PM>"

[git]
main_branch = "main"
scopes = ["<SCOPE1>", "<SCOPE2>", ...]

[mcp]
servers = ["sequential-thinking", "github"]
```

### 3b. Substitute placeholders

For each file in this list — replace all occurrences of the placeholders:

| File | Placeholders to replace |
|---|---|
| `CLAUDE.md` | `${PROJECT_NAME}` |
| `README.md` | `${PROJECT_NAME}`, `${PROJECT_VISION}`, `${STAKEHOLDERS}` |
| `ROADMAP.md` | `${PROJECT_NAME}`, `${PROJECT_VISION}` |
| `BUGS.md` | `${PROJECT_NAME}` |
| `ENVIRONMENT_SETUP.md` | `${PROJECT_NAME}` |
| `task.md` | `${TASK_NAME}` → `Initial setup` |
| `.memory/projectbrief.md` | `${PROJECT_NAME}`, `${PROJECT_VISION}`, `${STAKEHOLDERS}` |
| `.memory/techContext.md` | `${PROJECT_NAME}` |
| `.agents/rules/git.md` | `${PROJECT_SCOPES}` (comma-separated scopes string) |

Use the Read tool to read each file, then Edit to apply replacements. Skip files that don't exist.

### 3c. Create `.env` if missing

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

### 3d. Initialize git if needed

```bash
if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "chore: initialize from claude-ecosystem-template"
fi
```

---

## Phase 4 — Readiness check

Run each check and record ✅ / ⚠️ / ❌.

### 4a. Placeholders cleared

```bash
grep -r '\${PROJECT_NAME}' CLAUDE.md README.md .memory/projectbrief.md 2>/dev/null
```
✅ no output | ❌ placeholders remain

### 4b. `.ecosystem.toml` valid

```bash
python -c "import tomllib; tomllib.loads(open('.ecosystem.toml').read()); print('ok')" 2>/dev/null \
  || python3 -c "import tomllib; tomllib.loads(open('.ecosystem.toml').read()); print('ok')"
```
✅ `ok` | ❌ parse error

### 4c. `.env` exists

```bash
test -f .env && echo "exists" || echo "missing"
```
✅ exists | ⚠️ missing — copy `.env.example` manually

### 4d. Git repository initialized

```bash
git status --short
```
✅ any output (even clean) | ❌ not a git repo

### 4e. Git identity configured

```bash
git config user.name && git config user.email
```
✅ both set | ⚠️ not set — run `git config user.name "Name"` and `git config user.email "email"`

### 4f. Python available (if language = python or both)

```bash
python --version 2>/dev/null || python3 --version 2>/dev/null
```
✅ 3.11+ | ⚠️ older version | ❌ not found

### 4g. Health check passes (if language = python or both)

```bash
python scripts/health_check.py 2>&1 || python3 scripts/health_check.py 2>&1
```
✅ exits 0 | ❌ errors reported

### 4h. Node.js available (if language = node or both)

```bash
node --version 2>/dev/null
```
✅ v18+ | ⚠️ older | ❌ not found

### 4i. MCP configuration present

```bash
python -c "import json,sys; d=json.load(open('.mcp.json')); print(list(d.get('mcpServers',{}).keys()))"
```
✅ shows `['sequential-thinking', 'github']` | ⚠️ partial | ❌ `.mcp.json` missing

### 4j. Pre-commit hooks installed

```bash
test -f .git/hooks/pre-commit && echo "installed" || echo "missing"
```
✅ installed | ⚠️ missing — run `pre-commit install`

### 4k. Memory files populated

Check that these files exist and are non-empty beyond template comments:
- `.memory/activeContext.md`
- `.memory/lessons.md`
- `.memory/projectbrief.md`

✅ all present | ⚠️ some empty — fill in after initialization

### 4l. Claude Code hooks configured

```bash
python -c "import json; d=json.load(open('.claude/settings.json')); print('hooks' in d)"
```
✅ `True` | ❌ hooks missing from settings

---

## Phase 5 — Readiness scorecard

Print this table with actual ✅/⚠️/❌ from Phase 4:

```
╔══════════════════════════════════════════════════╗
║         ECOSYSTEM READINESS SCORECARD            ║
╠══════════════════════════════════════════════════╣
║  Project: <PROJECT_NAME>                         ║
║  Date:    <TODAY>                                ║
╠══════════════════╦═══════════╦═══════════════════╣
║ System           ║ Status    ║ Action            ║
╠══════════════════╬═══════════╬═══════════════════╣
║ Placeholders     ║  ✅/❌    ║                   ║
║ .ecosystem.toml  ║  ✅/❌    ║                   ║
║ .env             ║  ✅/⚠️    ║                   ║
║ Git repo         ║  ✅/❌    ║                   ║
║ Git identity     ║  ✅/⚠️    ║                   ║
║ Python runtime   ║  ✅/⚠️/❌ ║                   ║
║ Health check     ║  ✅/❌    ║                   ║
║ Node runtime     ║  ✅/⚠️/❌ ║                   ║
║ MCP config       ║  ✅/⚠️/❌ ║                   ║
║ Pre-commit hooks ║  ✅/⚠️    ║                   ║
║ Memory files     ║  ✅/⚠️    ║                   ║
║ Claude hooks     ║  ✅/❌    ║                   ║
╠══════════════════╩═══════════╩═══════════════════╣
║ OVERALL: READY ✅  /  NEEDS ATTENTION ⚠️         ║
╚══════════════════════════════════════════════════╝
```

Skip rows that don't apply to the current stack (e.g., Node rows if language = python).

Fill the **Action** column only for ⚠️/❌ rows — one short imperative (e.g. "run `pre-commit install`").

---

## Phase 6 — Next steps

After the scorecard, print:

```
Next steps:
  1. Fill .env  →  set GITHUB_PERSONAL_ACCESS_TOKEN
  2. Fill .memory/projectbrief.md  →  project vision, goals, constraints
  3. Fill .memory/techContext.md   →  stack, dependencies, environment
  4. Run /setup_environment        →  guided environment setup
  5. Run /new_session              →  load ecosystem context for daily work
```

If all checks are ✅ — add: `🟢 Ecosystem is ready. You can start working.`
If any ⚠️ remain — add: `🟡 Minor issues above — project can start but address ⚠️ items soon.`
If any ❌ remain — add: `🔴 Critical issues above — fix ❌ items before starting.`
