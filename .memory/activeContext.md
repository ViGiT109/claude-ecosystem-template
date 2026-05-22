# Active Context

> **Updated:** 2026-05-23 — v2.1 спринт закрыт. v2.1.0 + хотфикс v2.1.1 в `main`, re-audit 🟢 92/100. Готов к v2.2.
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.1 спринт закрыт. Idle.** Жду следующее направление от пользователя. Возможные кандидаты на v2.2 — см. §Loose ends и Lesson «pre-tag guardrail» из `.memory/lessons.md` (если рекуррентно).

## Completed in v2.1 sprint

- **Phase 1 — Hybrid retrieve** (в `main`, merge `e9d73c5`). BM25 + RRF в `scripts/reasoning_bank.py`; `--mode {dense,sparse,hybrid}` CLI; sparse работает без ChromaDB; `scripts/test_reasoning_bank.py` — 5/5 ассертов.
- **Phase 2 — Trajectory ingest** (в `main`, merge `52f3730`). v2.1 schema, dual-collection finalize, два `audit_history.jsonl` row за финализ. Прод-верификация — в v2.1.1.
- **Phase 3 — Downstream distribution** (в `main`, commit `da14942`). `scripts/update_ecosystem.py` — кросс-платформенный синк `.claude/` / `.agents/` / `scripts/` + `AGENTS.md`. SHA-слепок в `[ecosystem.file_shas]`.
- **Phase 4 — Release v2.1.0** (тег `v2.1.0`, commit `c6632b7`). Пост-релизный аудит 🟡 80/100 → автоматически собран хотфикс v2.1.1.
- **Phase 5 — Hotfix v2.1.1** (тег `v2.1.1`, commit `6e380f7`). Path-баг в `update_ecosystem.py`, секция `[ecosystem]` в `.ecosystem.toml`, прод-верификация Phase 2, три lesson'а. Re-audit 🟢 92/100.

## Sprint Goals (v2.1)

- [x] Phase 1 — Hybrid retrieve (`e9d73c5`)
- [x] Phase 2 — Trajectory ingest (`52f3730`)
- [x] Phase 3 — Downstream distribution (`da14942`)
- [x] Phase 4 — Release v2.1.0 (`c6632b7`, audit 🟡 80/100)
- [x] Phase 5 — Hotfix v2.1.1 (`6e380f7`, re-audit 🟢 92/100)

## Loose ends

- **Ветка `chore/ru-user-facing-and-language-hook`** (`abc21b7`) — i18n + хук детектирования языка. Висит отдельно. Конфликтует с post-v2.1 кодом. В отдельный спринт: либо смержить с разрешением конфликтов, либо удалить.
- **Pre-tag guardrail** (рекомендация v2.1.0 audit §5.1) — хук, проверяющий синхронность версий `plugin.json` ↔ `.ecosystem.toml` ↔ CHANGELOG ↔ tag. Сейчас закрывается через lesson «single-source-of-truth». Если повторится — кодировать как хук.
- **Trajectory finalize в CI** (рекомендация v2.1.0 audit §5.2) — health_check вызывает `record_session_trajectory()` на фикстуре. Не блокер для v2.1; кандидат в v2.2.

## Resume context

- **Спека v2.1:** `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` — выполнена, закрыта релизами v2.1.0 + v2.1.1.
- **Юзер-преференс:** работа только в `main`, никаких feature-веток. PR не нужен. Релизные/процессные решения — автономные ([feedback_autonomous_decisions](../C--claude-ecosystem-template/memory/feedback_autonomous_decisions.md)).
- **Аудиты:** `.memory/audit_v2.1.0_release.md` (🟡 80), `.memory/audit_v2.1.1_release.md` (🟢 92).
