# ${PROJECT_NAME} — AI Assistant Rules (Claude Code)

> **This file is the primary source of rules for the AI assistant.**
> Claude Code picks it up automatically at every conversation.

## Context Loading (Progressive Disclosure)

| Priority | Document | When to load |
|---|---|---|
| 🔴 ALWAYS | `CLAUDE.md` (this file) | Picked up automatically |
| 🔴 ALWAYS | `.memory/activeContext.md` | **Every** session — current focus |
| 🔴 ALWAYS | `.memory/lessons.md` | **Every** session — anti-patterns to avoid |
| 🟡 AUTO | `.agents/rules/code-quality.md` | When writing or reviewing code |
| 🟡 AUTO | `.agents/rules/git.md` | For git operations and releases |
| 🟡 AUTO | `.agents/context/coding-conventions.md` | When writing new code |
| 🟡 AUTO | `.memory/techContext.md` | When working with dependencies or infra |
| 🟢 ON-DEMAND | `.memory/projectbrief.md` | Project overview (new sessions, architecture) |
| 🟢 ON-DEMAND | `.memory/systemPatterns.md` | Architectural decisions |
| 🟢 ON-DEMAND | `.memory/progress.md` | Completed milestones |
| 🟢 ON-DEMAND | `ROADMAP.md` | Planning and prioritization |
| 🟢 ON-DEMAND | `docs/adr/`, `docs/specs/` | Before large changes |

> **Goal:** Minimize context footprint. Load 🟡 AUTO only for relevant tasks,
> 🟢 ON-DEMAND only when explicitly needed.

---

## Modular Rules

Detailed rules are split by concern. Read on demand:

| Module | File | When to read |
|---|---|---|
| **Common** | `.agents/rules/common.md` | Any code change |
| **Code Quality** | `.agents/rules/code-quality.md` | Writing or reviewing code |
| **Git** | `.agents/rules/git.md` | Commits and releases |
| **Coding Conventions** | `.agents/context/coding-conventions.md` | Full standards reference |
| **Changelog / Log** | `.agents/context/changelog-rules.md` | Releases, CHANGELOG updates |

---

## MANDATORY ACTIONS — Every Session

### Session start

Run `/new_session` — it loads `lessons.md`, `activeContext.md`, and recent commits.

### Session end — STATE SYNC:

> **HARD CLOSE TRIGGER:** Before your final message you MUST:

1. Update `.memory/activeContext.md` (what was done, current sprint focus).
2. If errors occurred — record a lesson: `/extract_lesson`.
3. Commit and push: `/commit_and_release`.

### Strict Task Verification (Runtime Guardrail)

- The guardrail is built into the **pre-commit hook** → fires at every `git commit`.
- Also checked in `finalize_session.py`.
- Scans `task.md` for `[ ]` / `[/]` → if found — commit is **BLOCKED**.
- **Obligation:** After each step — change `[ ]` to `[x]` in `task.md`.
- **Threshold:** `task.md` is required for tasks **> 1 step AND > 30 min**. Quick fixes < 30 min are exempt.

### Spec-Driven Development

- For tasks **> 2 hours** or **> 3 files** — a specification is required.
- Use `/create_spec` → creates a file in `docs/specs/`.
- Get user approval before starting implementation.

### Ecosystem Audit (behavioral session review)

- **Not the same as a file-existence check.** This is a review of **agent behavior during the session.**
- Run at user's request at the end of a session: `/audit_ecosystem`.
- The agent must go through 5 phases: evidence gathering → protocol evaluation → lesson identification → report → fixes.
- Each verdict is backed by **concrete evidence** (git log, diff, file content).
- Result: structured report with ✅/❌ for each item + fix plan.

> ⛔ **FORBIDDEN:** `git commit --no-verify` is banned. If a pre-commit hook is broken —
> fix it FIRST, then commit. `--no-verify` disables all guardrails.

---

## Memory Model (3 levels)

The ecosystem has **three independent stores** — do not confuse them.

| # | Store | Scope | What to store | What NOT to store |
|---|---|---|---|---|
| 1 | `.memory/` (in git) | Project (visible to all contributors) | Project context, activeContext, architecture, lessons, progress | User preferences, secrets, cross-project facts |
| 2 | Claude Code auto-memory (`~/.claude/projects/.../memory/MEMORY.md`) | User × project (local, not in git) | User preferences, role, feedback, communication style | Project artifacts, code, architectural decisions |
| 3 | Session context (ephemeral) | Single session | Drafts, temporary calculations, reasoning chains | Anything that must survive the session |

### Storage selection flowchart

```
New fact / lesson appears
  │
  ├─ About this project (architecture, decision, pattern, error)?   → .memory/
  │    └─ Recurring anti-pattern?                                   → .memory/lessons.md
  │    └─ Architectural decision?                                   → .memory/systemPatterns.md (+ ADR)
  │    └─ Current sprint focus?                                     → .memory/activeContext.md
  │
  ├─ About the user (how they work, what to avoid)?                → auto-memory
  │
  └─ Needed only for this response?                                 → just output it, write nothing
```

### Upgrade path (how lessons become rules)

Knowledge evolves in one direction — from observation to deterministic guardrail:

```
Session error
  → /extract_lesson   → .memory/lessons.md (observation)
  → recurred 2+ times → promote to .agents/rules/*.md (rule)
  → rule violated often → deterministic pre-commit / Claude Code hook (guardrail)
```

**Promotion criterion:** a lesson ≠ a rule. A lesson lives in `lessons.md` until it stabilizes.
When the same observation surfaces in 2+ sessions — move it to `rules/` (read at session start)
or encode it as a hook (cannot be violated).

---

## IDE Setup (Claude Code)

Full setup guide: `ENVIRONMENT_SETUP.md`
Automated MCP install: `.\scripts\setup_mcp.ps1`

### MCP servers (2 minimum)

| Server | Type | Purpose |
|---|---|---|
| `sequential-thinking` | Node.js | Structured multi-step reasoning (for audits) |
| `github` | Node.js | GitHub API (PR, issues, releases) |

**Why minimal:** Claude Code has many built-in tools:
- `filesystem`, `fetch`, `git` — duplicated by built-in tools (Read/Write/Edit/Grep + WebFetch + Bash `git`)
- `memory` (knowledge graph) — replaced by `.memory/lessons.md` + Claude Code auto-memory

Configuration: `.mcp.json` at project root. Tokens in `.env` (not in git).

---

## Slash Commands (`.claude/commands/`)

Invoked via `/<name>` in Claude Code:

- `/new_session` — context loading + lessons.md (progressive disclosure)
- `/extract_lesson` — extract lesson from error → lessons.md → promote to rules
- `/create_spec` — create specification (Spec-Driven Dev)
- `/audit_ecosystem` — deep behavioral audit (5 phases + Internet Scouting)
- `/commit_and_release` — commit and release workflow
- `/agentic_tdd` — TDD workflow (Red-Green-Refactor)
- `/setup_environment` — environment setup guide

---

## Subagents (`.claude/agents/`)

Subagents run in **isolated context** — the main dialog is not polluted by their tool calls;
only the final report is returned. Use when a task consumes a lot of context (audit, deep research).

| Agent | When to use | Model |
|---|---|---|
| `ecosystem-auditor` | Cross-session audit for 1-5 days (same as `/audit_ecosystem`, but without spending main context) | inherit |

Invocation: user writes "audit the ecosystem" or explicitly requests a subagent. Claude Code
routes by `description` from the frontmatter of each `.md` in `.claude/agents/`.

---

## Deterministic Hooks (`.claude/hooks/`)

Rules that **cannot be violated** — built into Claude Code lifecycle hooks:

| Hook | Trigger | What it does |
|---|---|---|
| `session_start.py` | SessionStart | Injects into context: `activeContext.md` (first 25 lines), lessons.md freshness, git status |
| `block_no_verify.py` | PreToolUse (Bash) | Blocks `git commit --no-verify` / `-n` (exit 2) |
| `stop_audit.py` | Stop | Checks abandoned `[ ]` in task.md, counts uncommitted changes, logs to `audit_history.jsonl` |

Configuration: `.claude/settings.json` (field `hooks`). Launched via `_run.py`
(proxy launcher — selects `.venv/Scripts/python.exe` → fallback to system `python`).
