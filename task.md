# Task: v2.0.0 Phase 4 — Planning Phase Detector + Context Monitor (PR #4)

**Branch:** `feat/v2.0.0-phase-4-planning-hint` (stacked on Phase 3)
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md) §Phase 4
**Plan:** `C:\Users\vibev\.claude\plans\parallel-leaping-rainbow.md` §Phase 4
**Goal:** add two cross-cutting signals — a UserPromptSubmit `planning_hint.py` hook that emits a unified `🧭 PLAN + 💡 MODEL` block on RU/EN architectural triggers, and a context-window monitor in `session_start.py` that emits `🔄 SESSION HANDOFF RECOMMENDED` when the transcript is over 70% of the active model's window.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Execution pattern
Per [.memory/activeContext.md](.memory/activeContext.md) §model-policy: main thread stays on **Opus 4.7** for the regex/format design (4.1) and the context-budget logic (4.0). 4.2 / 4.3 are mechanical doc edits — done inline on Opus (small, no parallelism win from delegation).

## Steps

### 4.0 — Context window monitor in `session_start.py` (Opus, main thread)
- [x] Add `MODEL_WINDOWS` constant (opus=1_000_000, sonnet=200_000, haiku=200_000) + `DEFAULT_MODEL = "opus"`
- [x] Add `_read_stdin_json()` helper — non-blocking read, return `{}` on empty/invalid
- [x] Add `_estimate_session_tokens()` — if stdin JSON has `transcript_path` and file exists, estimate tokens as `file_bytes // 4` (rough heuristic, but stable)
- [x] Add `emit_context_window_status()` — given est tokens + active model window, emit nothing if <70%, `🔄 SESSION HANDOFF RECOMMENDED` block if 70–90%, ❌ urgent variant if >90%
- [x] Wire into `main()` after `check_bootstrap_done()` short-circuit, before normal preamble — so user sees handoff hint even when other emitters fire
- [x] Respect `CLAUDE_MODEL` env var for selecting the window (fallback `opus`)

### 4.1 — `planning_hint.py` UserPromptSubmit hook (Opus, main thread)
- [x] Create `.claude/hooks/planning_hint.py` with shebang + module docstring referencing model-policy §Planning Phase Detector
- [x] Read stdin JSON `{"prompt": "..."}`; on empty/invalid → exit 0 silently
- [x] Env killswitch: `CLAUDE_DISABLE_PLANNING_HINT=1` → exit 0 silently
- [x] Whitelist: prompts shorter than 20 chars (after strip) → exit 0 silently (kills false positives like "ok", "fix typo")
- [x] RU trigger regex (case-insensitive, Unicode-aware): `спроектируй|спроектируем|разработай|архитектур|реализуй\s+.*(?:фич|функционал|модул)|рефактор|мигра|перепиши|редизайн`
- [x] EN trigger regex (case-insensitive): `\b(?:design|architect|implement|refactor|migration|rewrite|redesign|spec|specification|plan|planning)\b`
- [x] Heuristic: count file-like references (regex matching `[\w./-]+\.(?:py|md|json|toml|yaml|yml|ps1|ts|tsx|js|jsx|go|rs|java|kt|sh|sql)\b`) — ≥3 distinct matches counts as a trigger
- [x] On match → print the unified `🧭 PLAN PHASE RECOMMENDED` + `💡 MODEL` block to stdout; include the matched trigger or `multiple-file-refs` as the reason
- [x] Exit 0 in all paths (hook is advisory — never block)

### 4.2 — Register hook in `.claude/settings.json`
- [x] Add `UserPromptSubmit` array with `python .claude/hooks/_run.py .claude/hooks/planning_hint.py`, timeout 3s
- [x] Validate JSON still parses (`python -c "import json; json.load(open('.claude/settings.json'))"`)

### 4.3 — AGENTS.md sections (mechanical) + sync
- [x] Add section **«Planning-phase signaling»** to AGENTS.md — duplicates the hook behavior at the agent layer (when hook regex misses, the agent should still emit the block based on context)
- [x] Add section **«Session handoff signaling»** — when ctx >70% emit the `🔄 SESSION HANDOFF` block; recommend `/handoff` first
- [x] Extend the Deterministic Hooks table with `planning_hint.py` row
- [x] Run `python scripts/sync_agents_md.py --write` to regenerate CLAUDE.md
- [x] Confirm `python scripts/sync_agents_md.py --check` exits 0

### 4.4 — Cross-reference cleanup in `model-policy.md`
- [x] Drop the "(Phase 4)" parenthetical from the cross-reference table rows for `planning_hint.py` and `session_start.py` (the hooks now exist)
- [x] Add a short line under `## Cross-reference` linking to AGENTS.md's new «Planning-phase signaling» / «Session handoff signaling» sections so the policy stays the single entry point

### 4.5 — Verification
- [x] `python scripts/regenerate_plugin_manifest.py --check` → exit 0 (no new commands/agents, only a new hook — manifest scans hooks too)
- [x] If drift → regenerate, re-check
- [x] `python scripts/sync_agents_md.py --check` → exit 0
- [x] Trigger smoke test: `echo '{"prompt":"рефактор модуля auth"}' | python .claude/hooks/_run.py .claude/hooks/planning_hint.py` → block printed
- [x] No-trigger smoke test: `echo '{"prompt":"fix typo"}' | python .claude/hooks/_run.py .claude/hooks/planning_hint.py` → no output
- [x] Killswitch smoke test: `$env:CLAUDE_DISABLE_PLANNING_HINT="1"; echo '{"prompt":"рефактор"}' | python .claude/hooks/_run.py .claude/hooks/planning_hint.py` → no output
- [x] Context monitor smoke test: dry-run `python .claude/hooks/_run.py .claude/hooks/session_start.py` returns 0 (no crash on missing stdin)
- [x] task-guardrail check by manual pre-commit run (or via final commit)

### 4.6 — Wrap-up
- [x] Update `.memory/activeContext.md` — Phase 4 complete, Phase 5 next
- [x] Commit `feat(hooks): v2.0.0 Phase 4 — planning detector + context monitor` (NO `--no-verify`)

## Non-goals (this PR)
- ReasoningBank auto-ingest in `finalize_session.py` — Phase 5
- New subagents (code-reviewer, researcher) — Phase 6
- Statusline — Phase 6
- `.env.example` enrichment (the planning-hint killswitch row is mentioned in `model-policy.md`; `.env.example` row lands in Phase 6 bundle)

## Acceptance
- `planning_hint.py` fires on RU+EN triggers and on the ≥3-file-refs heuristic; silent for trivial prompts and when killswitch is set
- `session_start.py` emits a non-blocking `🔄 SESSION HANDOFF` block when transcript-size heuristic crosses 70% of the active model's window
- AGENTS.md documents both signaling rules; CLAUDE.md is in sync
- `model-policy.md` cross-reference table is up to date — no "(Phase 4)" placeholders left
- Pre-commit hooks (`agents-md-sync`, `plugin-manifest-sync`, `task-guardrail`) all green
