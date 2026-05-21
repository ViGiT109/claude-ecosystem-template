# Task: v2.0.0 Phase 6a — Mechanical Cleanup Bundle (PR #6a)

**Branch:** `feat/v2.0.0-phase-6a-mechanical-cleanup` (off Phase 5)
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md) §Phase 6
**Goal:** PR #6a — config/file mechanics only. Design work (subagents, statusline, docs) is split to PR #6b.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Execution pattern
Pure Sonnet-class mechanical edits — main thread handles inline, no subagent delegation.

## Steps

### 6.1 — File hygiene
- [x] **6.1a** Remove `scripts/monitor_context.sh` (superseded by `session_start.py` context monitor from PR #4)
- [x] **6.1b** `git mv .memory/claude_code_state.md .memory/api_reference_hooks.md` (it's an API snapshot, not project state)
- [x] **6.1c** Update stale refs in `TEMPLATE_README.md` (lines 95 + 108): drop `monitor_context.py` entry, rename `claude_code_state.md` → `api_reference_hooks.md`. Also update the file's own heading to match new name.

### 6.4 — Explicit outputStyle
- [x] Add top-level `"outputStyle": "default"` to `.claude/settings.json` (explicit > implicit; future readers see the chosen style).

### 6.5 — pyproject scaffold audit
- [x] Read `bootstrap.ps1` lines 185-214 (existing scaffold)
- [x] Compare against modern PEP 621 + tooling baseline. Add only what's missing — likely candidates: `[project.optional-dependencies] dev = [...]`, `[tool.ruff]`, `[tool.black]`, `[tool.pytest.ini_options]`
- [x] Keep the scaffold minimal — it's a starting point, not a full config

### 6.8 — .env.example enrichment
- [x] Add `ANTHROPIC_API_KEY=` with comment (used by Anthropic SDK, optional if running purely through Claude Code CLI)
- [x] Add `HTTPS_PROXY=` with comment (corporate networks)
- [x] Add `CLAUDE_DISABLE_PLANNING_HINT=` with comment (set to 1 to silence planning_hint.py hook)

### wrap
- [x] Manifest + AGENTS.md sync sanity: `python scripts/regenerate_plugin_manifest.py --check` + `python scripts/sync_agents_md.py --check` (no hook/skill changes expected → clean)
- [x] Update `.memory/activeContext.md` — Phase 6a done, Phase 6b next
- [x] Commit `chore(cleanup): v2.0.0 Phase 6a — mechanical bundle` (NO `--no-verify`)

## Out of scope (deferred to PR #6b)
- 6.2 subagents `code-reviewer.md` + `researcher.md` (Opus design)
- 6.3 `statusline.py` hook + settings registration
- 6.6 ADR + spec example files
- 6.7 `docs/template-design.md` (absorbs `TEMPLATE_README.md`)

## Acceptance
- `scripts/monitor_context.sh` gone; `.memory/api_reference_hooks.md` present (and old name absent)
- `TEMPLATE_README.md` references updated
- `.claude/settings.json` declares `outputStyle: default`
- `bootstrap.ps1` pyproject scaffold has tooling sections
- `.env.example` has 3 new variables with comments
- pre-commit clean (manifest + AGENTS.md sync green)
