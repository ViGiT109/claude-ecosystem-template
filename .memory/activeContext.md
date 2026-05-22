# Active Context

> **Updated:** 2026-05-23 — v2.1.0 выпущен, идёт хотфикс v2.1.1 (пост-релизный аудит дал 🟡 80/100, ниже целевых 85).
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.1.1 hotfix closure.** Hotfix-prep уже в индексе (см. `task.md` § Phase 5). Осталось: коммит prep → аннотированный тег `v2.1.1` → повторный аудит ≥85/100 → state-sync коммит, закрывающий Phase 5 closure-чекбоксы.

## Completed in v2.1 sprint

- **Phase 1 — Hybrid retrieve** (в `main`, merge `e9d73c5`). BM25 + RRF в `scripts/reasoning_bank.py`; `--mode {dense,sparse,hybrid}` CLI; sparse работает без ChromaDB; `scripts/test_reasoning_bank.py` — 5/5 ассертов.
- **Phase 2 — Trajectory ingest** (в `main`, merge `52f3730`). v2.1 schema, dual-collection finalize, два `audit_history.jsonl` row за финализ.
- **Phase 3 — Downstream distribution** (в `main`). `scripts/update_ecosystem.py` — кросс-платформенный синк `.claude/` / `.agents/` / `scripts/` + `AGENTS.md`. Защита `.memory/` / `.env*` / `task.md` / `.ecosystem.toml`. SHA-слепок в `[ecosystem.file_shas]`. Идемпотентный прогон `--from .` → 45 unchanged.

## Sprint Goals (v2.1)

- [x] Phase 1 — Hybrid retrieve (`e9d73c5`)
- [x] Phase 2 — Trajectory ingest (`52f3730`)
- [x] Phase 3 — Downstream distribution
- [ ] Phase 4 — Release v2.1.0 (CHANGELOG, version bump, тег, post-release audit ≥85)

## Next Steps

1. Обновить `CHANGELOG.md` — секция `v2.1.0` с Phase 1/2/3.
2. Поднять версию в `plugin.json` и `.ecosystem.toml` до `2.1.0`.
3. Закоммитить как `release: v2.1.0`, повесить аннотированный тег `v2.1.0`.
4. Запустить `/audit_ecosystem` — целевой балл ≥85/100.

## Loose ends

- **Ветка `chore/ru-user-facing-and-language-hook`** (`abc21b7`) — i18n + хук детектирования языка. Висит отдельно. Конфликтует с Phase 2. В отдельный спринт: либо смержить с разрешением конфликтов, либо удалить. Не из v2.1.

## Resume context

- **Спека:** `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` — approved.
- **Юзер-преференс:** работа только в `main`, никаких feature-веток. PR не нужен.
- **Модель:** для Phase 4 (CHANGELOG/тег) подходит Sonnet 4.6 — механика; для пост-релизного аудита — Opus 4.7.
