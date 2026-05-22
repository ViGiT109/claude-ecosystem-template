# Active Context

> **Updated:** 2026-05-23 — v2.2 спринт стартовал (Self-Diagnostic Ecosystem). Работаем в `main`.
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.2 Phase 1 — Pre-push version-sync guardrail.** Спека одобрена ([docs/specs/2026-05-23-v2.2-self-diagnostic-ecosystem.md](../docs/specs/2026-05-23-v2.2-self-diagnostic-ecosystem.md)), `task.md` структурирован под 7 фаз с Phase Release чекбоксами по design (lesson «release-checkboxes-in-task-md» применён заранее). Работаем прямо в `main`.

## Sprint Goals (v2.2)

- [ ] Phase 1 — Pre-push version-sync guardrail (Layer A)
- [ ] Phase 2 — Hook health-check (Layer A + B)
- [ ] Phase 3 — Auto-audit trigger в session_start.py (Layer B)
- [ ] Phase 4 — Consolidate-memory trigger (Layer B)
- [ ] Phase 5 — Diagnostic dashboard + `/diag_status` (Layer C)
- [ ] Phase 6 — Ecosystem health injection в session_start.py (Layer C)
- [ ] Phase 7 — Release v2.2.0 (audit ≥85, иначе хотфикс)

## Completed in v2.1 sprint (reference)

- v2.1.0 (`c6632b7`, тег `v2.1.0`) — hybrid retrieve + trajectory ingest + downstream distribution. Post-release audit 🟡 80/100.
- v2.1.1 (`6e380f7`, тег `v2.1.1`) — hotfix bundle (path-баг update_ecosystem, секция [ecosystem] в .ecosystem.toml, прод-верификация Phase 2, 3 lesson'а). Re-audit 🟢 92/100.

## Architecture key idea

**Session-triggered cron.** Не OS-level cron, не Anthropic scheduled-tasks (не портируется). Триггер — открытие новой сессии. `session_start.py` считает «долги» по журналам и эмитит `🔴 X REQUIRED` маркеры. Агент видит → запускает работу → пишет результат → долг сбрасывается. Кросс-платформенно, self-contained.

## Loose ends (постpone v2.3+)

- Ветка `chore/ru-user-facing-and-language-hook` (`abc21b7`) — i18n + хук детектирования языка. Висит отдельно.
- Lesson auto-promotion → rule (семантический анализ) — кандидат в v2.3.
- Tools usage tracking (in-process aggregator для `tools_used` поля) — v2.3+.

## Resume context

- **Спека v2.2:** `docs/specs/2026-05-23-v2.2-self-diagnostic-ecosystem.md` — approved.
- **План:** `~/.claude/plans/magical-drifting-reddy.md` — utvержён юзером.
- **Юзер-преференс:** работа только в `main`, никаких feature-веток. PR не нужен. Релизные/процессные решения — автономные ([feedback_autonomous_decisions](../C--claude-ecosystem-template/memory/feedback_autonomous_decisions.md)).
- **Аудиты:** `.memory/audit_v2.1.0_release.md` (🟡 80), `.memory/audit_v2.1.1_release.md` (🟢 92).
