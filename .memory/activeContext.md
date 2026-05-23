# Active Context

> **Updated:** 2026-05-23 — v2.3 спринт завершён. v2.3.0 в `main`.
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.3 спринт закрыт. Idle.** Жду пост-релизный аудит → решение по хотфиксу или продолжению.

## Sprint Goals (v2.3)

- [x] Phase 1 — Promote «Sprint Goals desync» lesson → rule + pre-commit guardrail (`ed84cc8`)
- [x] Phase 2 — Tools usage tracking (PostToolUse aggregator + `tools_used` в audit_history) (`5928f64`)
- [x] Phase 3 — Lesson auto-promotion detector (keyword-based, не semantic)
- [x] Phase N — Release v2.3.0

## Completed in v2.2 sprint

- **Phase 1 — Pre-push version-sync guardrail** (`b928caf`). Layer A детерминистическая гарантия. P1 баг найден в пост-релизном аудите v2.2.0 → закрыт в v2.2.1 через raw `.githooks/pre-push` shim.
- **Phase 2 — Hook health-check** (`ef75f2a`). `scripts/check_hook_health.py` + раздел Hooks в health_check.py + HOOK_DRYRUN=1 во всех 4 хуках.
- **Phase 3 — Auto-audit trigger** (`645b86b`). `_ecosystem_health.py` (новый общий stdlib-only модуль) + три состояния `emit_audit_freshness()`.
- **Phase 4 — Consolidate-memory trigger** (`5068370`). `emit_consolidate_freshness()` + `/consolidate_lessons` slash-команда.
- **Phase 5 — Diagnostic dashboard** (`a676f4b`). `scripts/diag_dashboard.py` 6 секций + `--summary` + `/diag_status`.
- **Phase 6 — Ecosystem health injection** (`e94a3fe`). Unified `## 📊 Ecosystem health` блок в инжекте session_start.py.
- **Phase 7 — Release v2.2.0** (`524224b`, тег `v2.2.0`). Post-release audit 🟡 75/100 → автохотфикс v2.2.1.
- **Phase 8 — Hotfix v2.2.1** (тег `v2.2.1`). Pre-push shim в `.githooks/`, `git tag --points-at HEAD` fallback в check_version_sync.py, E2E тест, ruff E741 fix, три lesson'а.

## Sprint Goals (v2.2)

- [x] Phase 1 — Pre-push version-sync guardrail (`b928caf`, fixed в v2.2.1)
- [x] Phase 2 — Hook health-check (`ef75f2a`)
- [x] Phase 3 — Auto-audit trigger в session_start.py (`645b86b`)
- [x] Phase 4 — Consolidate-memory trigger (`5068370`)
- [x] Phase 5 — Diagnostic dashboard + `/diag_status` (`a676f4b`)
- [x] Phase 6 — Ecosystem health injection в session_start.py (`e94a3fe`)
- [x] Phase 7 — Release v2.2.0 (`524224b`, audit 🟡 75/100)
- [x] Phase 8 — Hotfix v2.2.1 (re-audit target ≥ 85)

## Architecture key idea

**Session-triggered cron + raw .githooks/ shim для deterministic guardrails.** Открытие сессии триггерит просрочки (audit/consolidate/hook-health). Pre-push guardrail — raw shim, не через pre-commit framework (он silently skip'нул на Windows). Все journals — append-only с фильтрацией по event-type. Self-contained, кросс-платформенно, не зависит от OS-cron / external scheduled-tasks.

## Loose ends (postpone v2.3+)

- Ветка `chore/ru-user-facing-and-language-hook` (`abc21b7`) — i18n + хук детектирования языка. Висит отдельно.
- Lesson auto-promotion → rule (семантический анализ) — кандидат в v2.3.
- Tools usage tracking (in-process aggregator для `tools_used` поля) — v2.3+.
- Lesson «activeContext.md Sprint Goals desync» — РЕКУРРЕНТНЫЙ (v2.1.1 + v2.2.0). Промоушен в `.agents/rules/git.md::Release Workflow` рекомендуется в v2.3.

## Resume context

- **Спека v2.2:** `docs/specs/2026-05-23-v2.2-self-diagnostic-ecosystem.md` — закрыта v2.2.0 + v2.2.1.
- **План:** `~/.claude/plans/magical-drifting-reddy.md` — одобрен и исполнен.
- **Юзер-преференс:** работа только в `main`, никаких feature-веток. Релизные/процессные решения — автономные ([feedback_autonomous_decisions](../C--claude-ecosystem-template/memory/feedback_autonomous_decisions.md)).
- **Аудиты:** `.memory/audit_v2.1.0_release.md` (🟡 80), `.memory/audit_v2.1.1_release.md` (🟢 92), `.memory/audit_v2.2.0_release.md` (🟡 75), `.memory/audit_v2.2.1_release.md` (target ≥ 85).
