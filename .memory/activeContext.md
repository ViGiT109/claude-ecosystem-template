# Активный контекст

> **Обновлено:** 2026-05-22 — спецификация v2.1 утверждена; реализация продолжается.
> Загружается автоматически хуком `session_start.py` (первые 25 строк).

## Текущий фокус

**v2.1 — гибридный retrieve + ingest траекторий + раздача шаблона вниз по реке.** Спецификация утверждена 2026-05-22; 4 открытых вопроса закрыты согласно рекомендациям. Реализация разбита на 4 фазы и 4 PR. Phase 1 (`feat/v2.1-phase-1-hybrid-retrieve`) закоммичена локально (`a70de39`), не запушена.

Параллельно: ветка `chore/ru-user-facing-and-language-hook` — перевод пользовательского слоя на русский плюс новый хук `language_check.py` (детектирует кириллицу в промпте и инжектит напоминание отвечать по-русски).

## Сделано в этой сессии (2026-05-22)

- Удалены 8 локальных веток `feat/v2.0.0-phase-*` + `fix/v2.0.1-audit-followups` (локально и на origin) — архив v2.0.0/v2.0.1 теперь живёт только в тегах + истории main.
- Удалён мусор `tmp_files.txt`.
- Проверено, что v2.0.0 + v2.0.1 уже запушены; оба GitHub-релиза опубликованы; activeContext был устаревшим.
- Написана спецификация v2.1: [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](../docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md). Обновлён `docs/specs/README.md`.
- Закрыты 4 открытых вопроса: Python `update_ecosystem.py` (не npx), расширенная схема траекторий, hybrid как режим retrieve по умолчанию, sparse-only fallback в комплекте.
- `task.md` переписан как чеклист на 4 фазы v2.1.
- **Phase 1 реализована и закоммичена** (`a70de39`): BM25 + RRF + диспетчер режимов в `reasoning_bank.py`, новый `pyproject.toml`, тест-харнесс `scripts/test_reasoning_bank.py` (5 ассертов — все проходят), `uv.lock` сгенерирован.

## Цели спринта (v2.1)

- [x] Phase 1 — гибридный retrieve (BM25 + dense + RRF-фьюжн, флаг `--mode`, sparse fallback) — ветка `feat/v2.1-phase-1-hybrid-retrieve`
- [ ] Phase 2 — ingest траекторий (расширенная JSONL-схема, finalize по двум коллекциям) — ветка `feat/v2.1-phase-2-trajectory-ingest`
- [ ] Phase 3 — раздача шаблона вниз (`scripts/update_ecosystem.py`) — ветка `feat/v2.1-phase-3-update-ecosystem`
- [ ] Phase 4 — релиз v2.1.0 (CHANGELOG, bump версии, тег, пост-релизный аудит ≥85)

Дополнительная ветка вне фаз:
- [/] `chore/ru-user-facing-and-language-hook` — перевод user-facing слоя на русский + хук детектирования кириллицы

## Блокеры

Нет.

## Следующие шаги (начало следующей сессии)

1. Прочитать этот файл + спецификацию v2.1 + `task.md`.
2. Запушить ветки `feat/v2.1-phase-1-hybrid-retrieve` и `chore/ru-user-facing-and-language-hook`, открыть PR-ы (раздельно).
3. Стартовать Phase 2 от main на ветке `feat/v2.1-phase-2-trajectory-ingest` согласно `task.md` (после merge Phase 1).

## Контекст для возобновления

- **Спецификация:** `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` — утверждена, 4 фазы, 8–12 ч.
- **Модельная политика для этой работы:** Opus 4.7 по умолчанию (согласно `.agents/rules/model-policy.md`); механическая реализация BM25 — допустимо тихо делегировать саб-агенту на Sonnet, если контекст ужимается.
- **Языковая политика:** user-facing файлы (`.memory/`, `task.md`, сообщения хуков) — на русском; продуктовый слой шаблона (`AGENTS.md`, `CLAUDE.md`, `TEMPLATE_README.md`, `.agents/rules/*`) — на английском как часть кросс-инструментального стандарта.
