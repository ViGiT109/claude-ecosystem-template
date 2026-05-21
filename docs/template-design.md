# Template Design — Why It's Shaped This Way

> This doc explains the **rationale** behind `claude-ecosystem-template`. Read it
> if you want to understand *why* the structure looks the way it does — not just
> what's in each folder.
>
> Unlike `TEMPLATE_README.md`, this file survives `bootstrap.ps1` and stays in
> downstream projects, so the architecture story is not lost when the template
> repo is cloned away.

## Origin

This template was extracted from **Bingo7 v6** — a production Python ML/trading
project that ran for ~18 months across 7 major ecosystem iterations and
reached ~85/100 on its own behavioural-audit scoring. Domain code was stripped;
the generic governance layer was kept, refined, and ported here.

The shape below is the residue of what kept working after that many cycles.

## Principles

### 1. Progressive Disclosure

AI agents have finite context windows. Loading everything we know about a project
into every session is wasteful and crowds out actual work. So context is loaded
in **three tiers**:

- **🔴 ALWAYS** — `AGENTS.md` (+ generated `CLAUDE.md`), `.memory/activeContext.md`,
  `.memory/lessons.md`. Everything an agent needs in the first 30 seconds.
- **🟡 AUTO** — rules and conventions loaded only when the task triggers them
  (e.g. `.agents/rules/git.md` only for commits).
- **🟢 ON-DEMAND** — `.memory/projectbrief.md`, ADRs, specs. Read only when
  explicitly relevant.

The `/new_session` slash command and `session_start.py` hook implement this
tiering automatically.

### 2. Self-Improvement Loop

Errors should make the system smarter over time. The path is:

```
Session error
  → /extract_lesson  → .memory/lessons.md          (observation)
  → recurs 2+ times  → promote to .agents/rules/*.md (rule)
  → rule violated    → encode as pre-commit hook    (deterministic guardrail)
```

Each step removes one degree of freedom — observations become rules, rules
become hooks that can't be bypassed. The directory layout exists to make this
promotion mechanical, not heroic.

### 3. Three-level memory model

There are three independent stores. They are kept separate on purpose; mixing
them was the most common failure mode in earlier iterations.

| # | Store | Scope | What goes here |
|---|---|---|---|
| 1 | `.memory/` (in git) | Project, visible to all contributors | Architecture, decisions, lessons, sprint focus |
| 2 | Agent-tool auto-memory (e.g. `~/.claude/projects/.../memory/`) | User × project, local | Personal preferences, communication style |
| 3 | Session context | Single conversation | Drafts, intermediate reasoning |

Storing user preferences in `.memory/` would pollute git history with personal
state. Storing project lessons in auto-memory would lose them on machine wipe.
Each store has exactly one job.

### 4. Hooks in Python, not Bash

Every lifecycle hook (`session_start.py`, `block_no_verify.py`, `stop_audit.py`,
`planning_hint.py`, `statusline.py`) is Python. A small `_run.py` launcher
discovers the right interpreter (project `.venv` → system Python) without
requiring Bash or WSL on Windows.

Why this matters: Windows is the dominant dev OS for many users in this
template's intended audience, and shipping a project where the AI guardrails
silently fail because Git Bash isn't installed is unacceptable. Python is the
common-denominator runtime that's already present (the template itself uses
Python tooling) and gives us the same scripts on POSIX without changes.

### 5. AGENTS.md as source-of-truth, CLAUDE.md generated

See [ADR-001](adr/001-agents-md-source-of-truth.md). Short version: cross-tool
portability (Codex, Cursor, Windsurf, Aider all read `AGENTS.md`) plus a
deterministic generator (`scripts/sync_agents_md.py`) and a pre-commit guard
that refuses to ship drift.

### 6. Spec-Driven for big work, lightweight for small

- Tasks **< 30 min, single file** → just edit.
- Tasks **30 min – 2 h, multi-step** → create `task.md` with a checklist; a
  pre-commit hook refuses to commit if any `[ ]` / `[/]` items remain.
- Tasks **> 2 h or > 3 files** → `/create_spec` writes a spec to
  `docs/specs/`; user approves before implementation starts.

The three thresholds are crude on purpose. The lesson from prior iterations:
trying to plan a 20-minute change is theatre; trying to skip planning on a
2-day refactor is hubris. Putting numbers on the boundary stops both.

### 7. Deterministic guardrails > polite reminders

Where a behaviour must not be skipped, encode it as a hook the AI cannot
bypass:

- `block_no_verify.py` — refuses any `git commit --no-verify`.
- `agents-md-sync` pre-commit hook — refuses commits where `CLAUDE.md` lags
  `AGENTS.md`.
- `check_task_guardrail.py` — refuses commits with unchecked `task.md` items.
- `plugin-manifest-sync` — refuses commits where `plugin.json` lags actual
  hooks/skills/commands surface.

Reminders fade; hooks don't. We add new hooks when a lesson recurs three or
more times.

### 8. Subagents for context isolation

Some tasks are inherently context-hungry: cross-session audits, broad
research, independent code review. Running them in the main thread crowds out
the actual work. Subagents (`ecosystem-auditor`, `code-reviewer`, `researcher`)
run in **isolated context** — only the final report comes back to the main
dialog. Each subagent declares its own `model:` so we can route the expensive
ones to Opus and the routine ones to Sonnet.

### 9. Default to Opus, opt-in to Sonnet

The model policy ([`.agents/rules/model-policy.md`](../.agents/rules/model-policy.md))
inverts the typical 2026 default. Opus 4.7 is the start-of-session model;
Sonnet 4.6 is reserved for explicit safe-path triggers (small, mechanical,
single-file edits). This trades cost for reliability — appropriate for a
template whose users care more about correctness than throughput.

## What's intentionally absent

- **No domain code.** The template is the governance layer only. You bring the
  actual product.
- **Minimal MCP servers** (`sequential-thinking` + `github`). Modern agent tools
  cover filesystem, fetch, git, and memory natively; layering an MCP on top
  duplicates effort.
- **No "magic" auto-formatters on save.** The template prefers explicit
  pre-commit gates. Magic is great until you can't reproduce it on CI.
- **No telemetry phoning home.** All metrics (`audit_history.jsonl`,
  `session_trajectories.jsonl`, `retrieval_logs.jsonl`) are local files in
  `.memory/`. You own them.

## Where to learn more

- [`AGENTS.md`](../AGENTS.md) — the actual operational rules an agent reads.
- [`docs/adr/`](adr/) — recorded architectural decisions, oldest first.
- [`docs/specs/`](specs/) — large-task specs (start with the v2.0.0 upgrade
  spec for a worked example).
- [`.memory/lessons.md`](../.memory/lessons.md) — the journal of what went
  wrong in prior sessions and what we changed in response.

## Evolution

This file is not frozen. When a future ADR overturns a principle here, update
the affected section and link the ADR. The design doc should always reflect
the current shape, not the shape we used to have.
