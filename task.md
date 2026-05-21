# Task: v2.0.0 Phase 3 — Model Routing System (PR #3)

**Branch:** `feat/v2.0.0-phase-3-model-routing` (stacked on Phase 2)
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md) §Phase 3
**Plan:** `C:\Users\vibev\.claude\plans\parallel-leaping-rainbow.md` §Phase 3
**Goal:** make model selection declarative and explicit — every command + subagent declares its `model:`; `model-policy.md` is the single source of truth; users get `/model_check` and `/handoff`.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Execution pattern
Per [.memory/activeContext.md](.memory/activeContext.md) §model-policy: main thread stays on **Opus 4.7** for design work (3.1); mechanical edits (3.2 / 3.3 / 3.4 / 3.5) get **silently delegated to a Sonnet 4.6 subagent** — no user-facing announcement, no blocking.

## Steps

### 3.1 — `.agents/rules/model-policy.md` (design, Opus, main thread)
- [x] Philosophy section — Opus 4.7 default, Sonnet 4.6 opt-in on safe-path triggers
- [x] **Always Opus 4.7** allowlist: planning/spec, audit, refactor >3 files, hard debug, security/migrations/finance
- [x] **Sonnet 4.6 safe-path** whitelist: implementation per approved spec, trivial edits, docs over existing code, tests per contract, dead-code cleanup
- [x] **Context Window Awareness** section: Opus 1M / Sonnet 200K / Haiku 200K; if task >150K ctx → Opus regardless of nature; if session >70% → `🔄 NEW SESSION` block
- [x] **Model Switch Checkpoint** rules — minimally-blocking: only block when current model unfit AND subagent delegation impossible; default start = Opus 4.7
- [x] **Hybrid execution via subagents** — silent delegation pattern; always pass explicit `model:` to `Agent`; patterns table (Opus main → Sonnet Explore / researcher / mechanical impl)
- [x] **Block formats**: `💡 MODEL`, `🧭 PLAN`, `🔄 SESSION` — exact templates
- [x] Cross-reference table: where each rule applies (commands, subagents, hooks)

### 3.2 — Frontmatter `model:` in 8 slash-commands (delegated, Sonnet subagent)
- [x] `audit_ecosystem.md` → `model: opus`
- [x] `initialize_project.md` → `model: opus`
- [x] `create_spec.md` → `model: opus`
- [x] `extract_lesson.md` → `model: opus`
- [x] `new_session.md` → `model: inherit`
- [x] `commit_and_release.md` → `model: sonnet`
- [x] `agentic_tdd.md` → `model: inherit`
- [x] `setup_environment.md` → `model: sonnet`

### 3.3 — `.claude/agents/ecosystem-auditor.md` (delegated)
- [x] Frontmatter `model: inherit` → `model: opus`

### 3.4 — `/model_check` slash-command (delegated)
- [x] Create `.claude/commands/model_check.md` with `model: inherit`
- [x] Body describes: analyse last user prompt + estimated ctx %, emit `💡 MODEL RECOMMENDATION` block (Suggested / Reason / Context / Switch via)

### 3.5 — `/handoff` slash-command (delegated)
- [x] Create `.claude/commands/handoff.md` with `model: inherit`
- [x] Body describes: read git status + active task → update `.memory/activeContext.md` with resume context → suggest commit message → emit `🔄 SESSION HANDOFF` block with `/new_session` + "continue $WORK" instructions for the next session

### 3.6 — Verification
- [x] All 8 commands have `^model:` line in frontmatter (grep check)
- [x] `ecosystem-auditor.md` shows `model: opus`
- [x] Two new commands exist: `model_check.md`, `handoff.md`
- [x] `python scripts/regenerate_plugin_manifest.py --check` — drift confirmed (2 new commands); regenerated; re-check → exit 0
- [x] `pre-commit run plugin-manifest-sync --all-files` → Passed
- [x] `pre-commit run agents-md-sync --all-files` → Passed (after adding `model-policy.md` row to AGENTS.md modular-rules table + re-sync)
- [x] Added one-line pointer to AGENTS.md → `.agents/rules/model-policy.md`, re-synced via `scripts/sync_agents_md.py`

### 3.7 — Wrap-up
- [x] Update `.memory/activeContext.md` — Phase 3 complete, Phase 4 next
- [x] Commit `feat(model): v2.0.0 Phase 3 — model routing system` (89f9ced) — NO `--no-verify`
- [-] **Infra note:** `.git/hooks/pre-commit` not installed locally; pre-commit framework runs only via manual `pre-commit run`. All hooks (`agents-md-sync`, `plugin-manifest-sync`, `task-guardrail`) pass when invoked directly. Filed as user-decision (run `pre-commit install` to close the gap; not a code change).

## Non-goals (this PR)
- Planning Phase Detector hook (`planning_hint.py`) — Phase 4
- Context Window monitor inside `session_start.py` — Phase 4
- New subagents (code-reviewer, researcher) — Phase 6
- Statusline — Phase 6

## Acceptance
- Every slash-command + subagent declares its model explicitly
- `model-policy.md` answers "which model for X?" without ambiguity
- `/model_check` and `/handoff` invocable
- All pre-commit hooks (`agents-md-sync`, `plugin-manifest-sync`, `task-guardrail`) pass
