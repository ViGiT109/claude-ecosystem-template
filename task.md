# Task: v2.0.0 Phase 2 — Distribution-readiness (PR #2)

**Branch:** `feat/v2.0.0-phase-2-distribution-readiness` (stacked on Phase 1)
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md) §Phase 2
**Goal:** make this template publishable as a Claude Code plugin — auto-regenerated manifest, marketplace.json scaffold, working audit-freshness signal.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Context

Three deliverables. Existing drift / latent bug to fix:

- `plugin.json` is **already out of sync** — `initialize_project.md` (added on `feat/v2.0.0-phase-1-critical-fixes`) isn't in the `files` list. The drift is unmanaged today.
- The audit-freshness signal in `stop_audit.py::audit_age_days()` is **latently broken**: every Stop hook appends a `stop_hook` event, so the "last entry" is always seconds old. Need to filter by `event == "audit_complete"`.

## Steps

### 2.1 — `scripts/regenerate_plugin_manifest.py` + pre-commit guard
- [x] Write the script. Scans `.claude/hooks/*.py`, `.claude/commands/*.md`, `.claude/agents/*.md`, `.claude/skills/*/SKILL.md`; emits posix-separator paths sorted deterministically into `files`. Preserves non-`files` fields verbatim from existing manifest. Modes: default = write; `--stdout` = print; `--check` = exit 1 with diff on drift.
- [x] Run script once → fix current drift (add `initialize_project.md`).
- [x] Add `plugin-manifest-sync` hook to `.pre-commit-config.yaml`; triggers on `.claude/**` or `.claude-plugin/plugin.json` changes.
- [x] Smoke: `python scripts/regenerate_plugin_manifest.py --check` → exit 0.
- [x] Smoke: touch a fake `.claude/commands/_test.md`, `--check` exits 1 with diff; remove fake.
- [x] Commit: `feat(plugin): auto-regenerate manifest + pre-commit guard` (rolled into combined Phase 2 commit)

### 2.2 — `.claude-plugin/marketplace.json`
- [x] Write a valid `.claude-plugin/marketplace.json` referencing this plugin via `source: "./"`. Owner: `vibev` (matches plugin.json).
- [x] Validate: `python -c "import json; json.load(open('.claude-plugin/marketplace.json'))"` → no error.
- [x] Do **not** publish — file is ready for future use.
- [x] Commit: `feat(plugin): add marketplace.json scaffold` (rolled into combined Phase 2 commit)

### 2.3 — Audit freshness signal in `session_start.py`
- [x] Add `emit_audit_freshness()` to `session_start.py`. Reads `.memory/audit_history.jsonl`, filters entries where `event == "audit_complete"`, computes age of the most recent. If no such entry **or** age >14 days → emit `## 📊 audit: 🟡 …` block recommending `/audit_ecosystem`. Otherwise silent.
- [x] Patch `.claude/hooks/stop_audit.py::audit_age_days()` to filter by `event == "audit_complete"` (consistency). Update its docstring to reflect the change.
- [x] Patch `scripts/finalize_session.py::check_audit_debt()` analogously (currently uses file mtime — also broken).
- [x] Patch `.claude/commands/audit_ecosystem.md` Phase E: instruct the agent to append `{"event": "audit_complete", "timestamp": "<UTC>", "rating": "🟢/🟡/🔴"}` to `.memory/audit_history.jsonl` as the final step.
- [x] Smoke: run `python .claude/hooks/session_start.py` manually → expect 🟡 audit block (no `audit_complete` events recorded yet).
- [x] Commit: `fix(audit): meaningful audit-freshness signal (filter by event type)` (rolled into combined Phase 2 commit)

### Verification (PR #2 acceptance)
- [x] `python scripts/regenerate_plugin_manifest.py --check` → exit 0
- [x] `pre-commit run plugin-manifest-sync --all-files` → Passed
- [x] `pre-commit run agents-md-sync --all-files` → Passed (Phase 1 hook still works)
- [x] `python -c "import json; json.load(open('.claude-plugin/marketplace.json'))"` → ok
- [x] `python .claude/hooks/session_start.py` → emits 🟡 audit-freshness block (since no `audit_complete` entry exists yet)
- [x] `pre-commit run --all-files` → all hooks Passed (ruff Failed because `ruff`/`uv` not on PATH; pre-existing infra gap, identical to Phase 1)

### Wrap-up
- [x] Update `.memory/activeContext.md` — Phase 2 complete, Phase 3 next
- [x] Lesson recorded: "Append-only logs need event-type filters for freshness checks" in `.memory/lessons.md`
- [-] Push branch; open PR #2 stacked on PR #1 — **N/A**: no `origin` remote configured (same as Phase 1). Branch is local; user decides when to publish.
