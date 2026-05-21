# Task: v2.0.1 — Audit Follow-ups (P1 hotfix)

**Branch:** `fix/v2.0.1-audit-followups` (off `main` at v2.0.0)
**Source:** Post-v2.0.0 sanity audit via `ecosystem-auditor` subagent (🟢 92/100, 2026-05-21)
**Goal:** Address the two P1 findings before they ossify; defer P2/P3 to a future minor.

## Steps

- [x] Fix CHANGELOG numeric drift — Phase 3 bullet "9 slash commands" → "10 (8 existing + 2 new)". Confirmed live count via `ls .claude/commands/` + `grep -c .claude/commands/ .claude-plugin/plugin.json` = 10.
- [x] Add `## [2.0.1]` section to `CHANGELOG.md` (Fixed + Added)
- [x] Append first `audit_complete` row to `.memory/audit_history.jsonl` — schema per `.claude/commands/audit_ecosystem.md` Phase E (timestamp, event, rating); enriched with score, mode, window, tag_under_audit, source, findings. Gives the v2.0.0 Phase-2 freshness fix its first real datapoint.
- [x] Update `.memory/activeContext.md` — record v2.0.1 hotfix
- [x] Commit `fix: v2.0.1 — CHANGELOG numeric + first audit_complete row` (NO `--no-verify`)
- [x] Tag `v2.0.1` (annotated)
- [x] Push branch + tag; merge to main (fast-forward) and push main

## Deferred to v2.1 backlog

- [-] **P2** Hook smoke-test harness (`scripts/smoke_hooks.py` or `tests/hooks/test_hooks_smoke.py`)
- [-] **P2** ChromaDB happy-path verification for `reasoning_bank_ingest`
- [-] **P3** Prose-vs-manifest counter check (scan README/CHANGELOG/TEMPLATE_README for `N commands/hooks/agents` claims, assert against `plugin.json`)
- [-] **P3** Logger adoption in `scripts/` (120 `print()` occurrences; backend_modules empty in template so print-ban does not apply — flag for downstream Python projects)

## Acceptance

- `CHANGELOG.md` lists v2.0.1 above v2.0.0; Phase 3 bullet reads "10 slash commands"
- `.memory/audit_history.jsonl` contains the first `audit_complete` row (score 92)
- `git tag` lists both `v2.0.0` and `v2.0.1`
- `main` is fast-forwarded to include the hotfix
- pre-commit clean
