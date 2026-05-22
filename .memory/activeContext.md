# Active Context

> **Updated:** 2026-05-22 — Phase 1 + Phase 2 в `main`. Сессия закрыта по запросу юзера, продолжение в новой.
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.1 Phase 3 — Downstream distribution.** Работаем прямо в `main` (юзер: «никаких feature-веток, всё в main»). Нужно написать `scripts/update_ecosystem.py` — кросс-платформенный скрипт, который синкает `.claude/`, `.agents/`, `scripts/` из апстрим-темплейта в downstream-проект.

## Completed in v2.1 sprint

- **Phase 1 — Hybrid retrieve** (в `main`, merge `e9d73c5`). BM25 + RRF в `scripts/reasoning_bank.py`; `--mode {dense,sparse,hybrid}` CLI; sparse работает без ChromaDB; `scripts/test_reasoning_bank.py` — 5/5 ассертов.
- **Phase 2 — Trajectory ingest** (в `main`, merge `52f3730`). v2.1 schema, dual-collection finalize, два `audit_history.jsonl` row за финализ.
- Ветки `feat/v2.1-phase-1-*`, `feat/v2.1-phase-2-*`, `feat/v2.1-phase-3-*` удалены локально и на origin.

## Sprint Goals (v2.1)

- [x] Phase 1 — Hybrid retrieve (`e9d73c5`)
- [x] Phase 2 — Trajectory ingest (`52f3730`)
- [ ] Phase 3 — Downstream distribution (`scripts/update_ecosystem.py`) — работаем в `main`
- [ ] Phase 4 — Release v2.1.0 (CHANGELOG, version bump, тег, post-release audit ≥85)

## Next Steps (новая сессия)

1. Написать `task.md` для Phase 3 (сейчас он — ретроспектива Phase 1+2).
2. Реализовать `scripts/update_ecosystem.py` per spec §"Phase 3":
   - `--from <git-url-or-path>` (git URL → clone в tmp; путь → используем напрямую).
   - `--dry-run` по умолчанию, `--apply` чтобы реально копировать, `--force` чтобы перезаписать SHA-protected файлы, `--exclude PATTERN` для доп. пропусков.
   - Whitelist путей: `.claude/`, `.agents/`, `scripts/`, корневые `bootstrap.*`, `.pre-commit-config.yaml`, `pyproject.toml`, `.mcp.json`, `CLAUDE.md`, `AGENTS.md`.
   - Blacklist (всегда): `.memory/`, `.env*`, `task.md`, `.git/`, `__pycache__/`.
   - SHA-protect `CLAUDE.md` / `AGENTS.md` через новую секцию `[ecosystem] file_shas` в `.ecosystem.toml`.
   - После `--apply` обновлять `.ecosystem.toml::ecosystem.{version, upstream_sha, file_shas}`.
3. Acceptance: `update_ecosystem.py --dry-run --from .` из самого репо → ноль diff'ов (самоидемпотентно).
4. Phase 4 — релиз v2.1.0 (CHANGELOG, `plugin.json` + `.ecosystem.toml` version bump, аннотированный тег).

## Loose ends

- **Ветка `chore/ru-user-facing-and-language-hook`** (`abc21b7`) — i18n + хук детектирования языка. Висит отдельно. Конфликтует с Phase 2 по `session_start.py` / `activeContext.md` / `lessons.md`. В новой сессии: либо смержить с разрешением конфликтов, либо отказаться и удалить. Не из v2.1 спринта.

## Resume context

- **Спека:** `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` — approved.
- **Юзер-преференс:** работа только в `main`, никаких feature-веток. PR не нужен.
- **Модель:** для Phase 3 default Opus 4.7 (diff/SHA-логика — не механика).
