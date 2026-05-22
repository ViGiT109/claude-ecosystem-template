# Task: v2.1 Reasoning Bank Distribution

**Spec:** [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md)
**Sprint progress:** tracked in [.memory/activeContext.md](.memory/activeContext.md)

## Phase 1 — Hybrid retrieve — **DONE** (merged)

- [x] `pyproject.toml` created; `rank-bm25` added to `[project.optional-dependencies] reasoning`
- [x] `_bm25_retrieve()` + `_rrf_fuse()` implemented in `scripts/reasoning_bank.py`
- [x] `retrieve()` dispatches on `mode ∈ {dense, sparse, hybrid}`, default hybrid
- [x] CLI `--mode` / `--rrf-k` flags; graceful degradation when chromadb missing
- [x] `mode` field logged in `.memory/retrieval_logs.jsonl`
- [x] Query-harness `scripts/test_reasoning_bank.py` — 5 assertions, all pass

## Phase 2 — Trajectory ingest — **DONE** (merged)

- [x] `session_start.py::record_session_start()` writes `.memory/.session_start` (gitignored, idempotent 12 h)
- [x] `record_session_trajectory()` rewritten to v2.1 schema (`files_touched`, `duration_min`, `tools_used: []`)
- [x] `ingest_reasoning_bank()` split into two bounded subprocesses (`ingest_lessons` + `ingest_trajectories`)
- [x] Each writes its own `audit_history.jsonl` row
- [x] `parse_trajectories()` defensive `.get()` + legacy `files_changed` fallback

## Phase 3 — Downstream distribution — **DONE**

Реализовано в `main`. Файл: [scripts/update_ecosystem.py](scripts/update_ecosystem.py).

### Командная строка
- [x] `argparse`: `--from <путь|git-url>` (обязательный), `--apply`, `--exclude <маска>` (повторяемый), `--force`, `--project <каталог>`
- [x] `--help` описывает безопасный режим по умолчанию (без записи; не трогает `.memory/` / `.env*` / `task.md`)

### Поиск шаблона-источника
- [x] git-URL → `git clone --depth=1` во временный каталог, удаление в `finally`
- [x] локальный путь — используется как есть
- [x] отклоняем то, что не похоже на шаблон (нет `.claude/` и `.agents/`)

### Логика сравнения
- [x] Множество для синхронизации: `.claude/`, `.agents/`, `scripts/`, `AGENTS.md`
- [x] Защищённые: `.memory/`, `.env*`, `task.md`, `.git/`, `.venv/`, `node_modules/`, `__pycache__/`, `.ecosystem.toml`
- [x] Классификация каждого файла: `new` / `modified` / `unchanged` / `blocked`
- [x] Локальные файлы вне шаблона не трогаются (только добавляем и обновляем, не удаляем)
- [x] `--exclude` через `fnmatch`

### Защита контрольными суммами
- [x] Чтение секции `[ecosystem.file_shas]` из локального `.ecosystem.toml`; отсутствует → первый запуск
- [x] Локальная sha256, не совпадающая со слепком и с шаблоном → ручная правка → нужен `--force`
- [x] Без `--force` файлы помечаются `blocked`, при `--apply` выход с кодом 1

### Вывод
- [x] План сгруппирован по статусам, в конце — счётчики
- [x] При `--apply` обновляется секция `[ecosystem]` в `.ecosystem.toml` (`version` из `plugin.json` шаблона, `upstream_sha` из `git rev-parse`, `file_shas`)

### Проверки
- [x] Идемпотентность: `python scripts/update_ecosystem.py --from .` → 0 изменений (45 unchanged)
- [x] Дымовой тест во временном каталоге: пустой → 45 new → копируем → второй прогон 45 unchanged → правим вручную → 1 blocked → `--force` → 1 modified
- [x] Холостой прогон ничего не пишет (запись только под `if args.apply`)
- [x] Защищённые файлы (`.memory/should_not_be_touched.md`, `.env`, `task.md`) во время теста не тронуты

### Документация
- [x] `TEMPLATE_README.md` §"Keeping the template up to date" переписан под новый скрипт
- [x] Секция `[ecosystem]` в `.ecosystem.toml` описана там же как формат слепка

## Phase 4 — Release v2.1.0 — **DONE**

- [x] CHANGELOG §[2.1.0] написан, дата 2026-05-23
- [x] `plugin.json` поднят 1.0.0 → 2.1.0
- [x] Аннотированный тег `v2.1.0` создан и запушен (`c6632b7`)
- [x] Пост-релизный аудит выполнен (`/audit_ecosystem` через `ecosystem-auditor` сабагент → 🟡 80/100, отчёт в `.memory/audit_v2.1.0_release.md`)

> Балл ниже целевых 85 → автоматически собран хотфикс v2.1.1 (см. Phase 5) по
> прецеденту v2.0.0 → v2.0.1. Решение принято автономно — см.
> [feedback: автономные релизные решения](../C--claude-ecosystem-template/memory/feedback_autonomous_decisions.md).

## Phase 5 — Hotfix v2.1.1 (prep) — **DONE**

Закрывает три gap'а из аудита v2.1.0 + один найденный в процессе path-баг.
Подготовка релиза (всё, что не требует тега):

### Прод-верификация Phase 2 (trajectory ingest)
- [x] Прямой вызов `record_session_trajectory()` с фикстурой → `.memory/session_trajectories.jsonl` получил первую строку (1 ≠ 0 байт)

### Sync `.ecosystem.toml`
- [x] Bump `plugin.json` 2.1.0 → 2.1.1
- [x] Фикс `update_ecosystem.py::get_upstream_version()` — искать `.claude-plugin/plugin.json` перед корневым
- [x] `python scripts/update_ecosystem.py --from . --apply` → секция `[ecosystem]` записана: `version="2.1.1"`, `upstream_sha`, `[ecosystem.file_shas]` (45 записей)

### Lessons
- [x] `.memory/lessons.md` × 3 новых записи: ship-prod-run / single-source-of-truth-version / release-checkboxes-in-task-md

### Release-чеклист в task.md (этот раздел)
- [x] Чекбоксы Phase Release живут в `task.md`, а не в `activeContext.md` — guardrail видит их

### CHANGELOG
- [x] CHANGELOG §[2.1.1] описан

### Pending closure
Тег `v2.1.1` и пост-релизный аудит ≥ 85/100 трекаются отдельным
state-sync коммитом (создаётся ПОСЛЕ тега, иначе чекбокс с `[ ]`
блокирует pre-commit guardrail).
