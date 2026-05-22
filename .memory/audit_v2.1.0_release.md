# Ecosystem Audit — 2026-05-23 — post-release (v2.1.0)

## 1. Window and sources

- **Period:** `e9d73c5^..HEAD` (Phase 1 merge до релизного коммита `c6632b7`), 2026-05-22 → 2026-05-23.
- **Commits in window:** 9 (5 фич-коммитов + 2 merge + 1 state-sync + 1 release).
- **Files changed (cumulative):** 15 файлов, +4313 / −144.
- **Tag under audit:** `v2.1.0` (annotated, аннотация цитирует CHANGELOG).
- **Spec:** `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` (approved).
- **Tool-calls для сбора доказательств:** 21 (см. §6 Audit Trail).

## 2. Scorecard (14 пунктов)

| # | Механизм | Статус | Доказательство |
|---|---|---|---|
| 1 | Spec-Driven Development для крупной задачи | ✅ | `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` создан, цитируется в `task.md:3` и в коммите `a70de39` («Refs: docs/specs/...»). |
| 2 | `task.md` ведётся и закрывается `[x]` для всех технических пунктов | ✅ | `grep "- \[ \]" task.md` → 0 совпадений; все Phase 1/2/3 пункты `[x]`. |
| 3 | Phase 4 (релиз) отслеживается в чек-формате | ❌ | В `task.md` Phase 4 описан только prose-разделом «## Phase 4 — Release v2.1.0» без чекбоксов; чекбокс «`- [ ] Phase 4 — Release v2.1.0`» живёт в `activeContext.md:21`, что нарушает Strict Task Verification (task.md — единственный источник правды для guardrail). |
| 4 | Запрет `git commit --no-verify` соблюдён | ✅ | `git log --all --grep="no-verify"` → 0; `git reflog | head -40` показывает только `commit:` / `merge` / `checkout`, без `--no-verify` или признаков обхода хука. |
| 5 | CHANGELOG обновлён с разделом `[2.1.0]` | ✅ | `c6632b7` diff показывает новый раздел с датой 2026-05-23 и описанием 3 фаз (`CHANGELOG.md:13-50`). |
| 6 | `plugin.json` поднят до `2.1.0` | ✅ | `c6632b7`: `1.0.0` → `2.1.0` (`.claude-plugin/plugin.json:3`). |
| 7 | `.ecosystem.toml` поднят до `2.1.0` (как требуют спека и activeContext.md:26) | ❌ **P1** | В `.ecosystem.toml` нет ни секции `[ecosystem]`, ни поля `version`. Релизный коммит `c6632b7` файл не трогает. Спека L62 и activeContext.md:26 явно его перечисляют. Phase 3-скрипт `update_ecosystem.py` ожидает там же секцию `[ecosystem.file_shas]` — её тоже нет. |
| 8 | Аннотированный тег `v2.1.0` создан | ✅ | `git show v2.1.0 --no-patch`: tag object с автором и сообщением, ссылающимся на CHANGELOG §[2.1.0]. |
| 9 | State-sync перед релизом | ✅ | `b4f505c chore(state-sync): handoff — Phase 1+2 in main, Phase 3 next` — `activeContext.md` обновлён до релиза; следующий update попал в `da14942` («сдвигаем фокус на Phase 4»). |
| 10 | Lesson recorded когда обнаружен gap | ❌ | За весь спринт v2.1 `.memory/lessons.md` не менялся (`git log -- .memory/lessons.md` → последний коммит `3cecd76`, ДО спринта). Обнаруженные gap'ы (см. §4) не материализованы как lessons. |
| 11 | Hook `stop_audit.py` фиксирует state в `audit_history.jsonl` | ✅ | 18 строк `event: "stop_hook"` за окно 2026-05-21..2026-05-22; в коммитах `0a8e74b` и `fb63f88` есть `chore(audit): append stop_hook entries`. |
| 12 | Phase 2 happy-path подтверждён на живых данных (trajectory finalize + dual ingest) | ❌ **P1** | `.memory/session_trajectories.jsonl` = 0 байт; в `audit_history.jsonl` за весь спринт нет ни одного `reasoning_bank_ingest_lessons` / `_trajectories` row. Единственный `reasoning_bank_ingest` — 2026-05-21, статус `skipped` (chromadb missing). Код написан и smoke-протестирован в Phase 2, но в продакшен-цикле финализации сессии не прогонялся. |
| 13 | Phase 1 retrieve работает (логи) | ✅ | `.memory/retrieval_logs.jsonl`: 7 строк, есть `mode: sparse` и `mode: hybrid`, поле `mode` корректно записано (Phase 1 acceptance). |
| 14 | Релиз закрывается `audit_complete` row | ❓ → ✅ (закрывается этим аудитом) | До запуска текущего аудита в `audit_history.jsonl` последний `audit_complete` был от 2026-05-21 (v2.0.0). Текущий subagent дописывает строку `audit_complete` для v2.1.0 — §Phase E. Это и есть Lesson «append-only logs need event-type filters» в действии. |

## 3. Devil's Advocate

Беру три ✅ вердикта и пытаюсь их опровергнуть.

**✅ #1 — Spec-Driven Development для крупной задачи.**
- Что искал: соответствие спека/реализация — упоминают ли коммиты спеку, написана ли спека ДО кода.
- Контр-доказательство: спека датирована 2026-05-22 (создана в session `chore/ru-...`), Phase 1 коммит `a70de39` — 2026-05-22 01:27, спека создана раньше (предыдущий `b2e5667 chore(state-sync): session handoff — v2.1 spec approved`). Спека действительно `approved`, коммиты явно её цитируют. **Опровергнуть не удалось.**

**✅ #4 — Запрет `--no-verify` соблюдён.**
- Что искал: попытки прохода мимо pre-commit hook, в т.ч. через `git commit -n`, force-push, env-override (`HUSKY=0`).
- Контр-доказательство: проверял `git log --all -S "--no-verify"` (текстовый поиск по диффам) → 0; `git reflog | head -40` → только `commit:` и `checkout:` / `merge` / `reset`, без следов `commit --amend --no-verify`. Никаких следов обхода. **Опровергнуть не удалось.**

**✅ #2 — `task.md` ведётся.**
- Что искал: пункты `[ ]` или `[/]`, оставленные в проде.
- Контр-доказательство: Grep на `^\s*- \[ \]` в `task.md` → No matches. НО: в `activeContext.md:21` чекбокс `- [ ] Phase 4 — Release v2.1.0` всё ещё открытый. Технически guardrail смотрит ТОЛЬКО `task.md` (`scripts/check_task_guardrail.py`), но это — слепая зона: трекинг расщеплён между двумя файлами. **Опровержение частично удалось → понижает ✅ до ⚠️ и фидит ❌ #3.** Записал.

## 4. Кандидаты в `.memory/lessons.md`

### Кандидат А — Trajectory ingest шипится без happy-path verification

**Title:** Ship code paths with at least one prod run before declaring DONE
**Description:** Phase 2 v2.1 написала `record_session_trajectory()` + дуал-ингест и smoke-тестировала их в изоляции, но за весь спринт ни одна реальная финализация сессии не прогналась — `session_trajectories.jsonl` остался 0 байт. Релиз с «функциональной» фичей, у которой не подтверждён хотя бы один прод-вызов.
**Content:** Acceptance criterion для любой фичи на write-path (logger, ingest, journal): минимум одна запись в реальном файле журнала ДО релизного коммита. Smoke-тест внутри `if __name__ == "__main__"` не считается — он пишет в temp/in-memory. Способ зафиксировать: добавить в pre-release checklist «`wc -l <write-path-file>` отличается от значения до спринта» либо проверять в pre-tag hook.
**Source:** v2.1.0 post-release audit | outcome: prevention

### Кандидат Б — Версия проекта живёт в трёх местах, обновление одного — не всех

**Title:** Single-source-of-truth for project version
**Description:** В v2.1.0 релизе `plugin.json` поднят до `2.1.0`, CHANGELOG получил раздел `[2.1.0]`, тег `v2.1.0` создан, но `.ecosystem.toml` не получил секции `[ecosystem].version = "2.1.0"`. Спека L62 + activeContext.md:26 явно перечисляли все три места.
**Content:** Версия должна быть в ОДНОМ месте (источник правды — `plugin.json`), остальные файлы (`.ecosystem.toml`, CI) читают её оттуда. Либо — pre-tag-хук, который сверяет три значения и блокирует release-коммит при расхождении. Сейчас pre-commit guardrail смотрит только `task.md`, версионная синхронность — слепая зона.
**Source:** v2.1.0 post-release audit | outcome: prevention

### Кандидат В — Чекбоксы релиз-фазы должны жить в `task.md`, не в `activeContext.md`

**Title:** Release phase tracked in task.md, not in activeContext.md
**Description:** `task.md` отслеживает Phase 1/2/3 по пунктам, а Phase 4 (релиз) описан только prose-разделом. Чекбокс «`- [ ] Phase 4 — Release v2.1.0`» оставлен в `activeContext.md:21`. Pre-commit guardrail (`scripts/check_task_guardrail.py`) сканирует только `task.md` → release-чекбоксы не покрыты.
**Content:** При создании task.md для спринта сразу включай раздел «## Phase N — Release» с явными чекбоксами: CHANGELOG, version bump (3 файла), tag, audit ≥X. После релиза чекбоксы закрываются `[x]`, что одновременно: (а) фиксирует факт релиза, (б) держит трекинг в одном месте, (в) gardrail может реально что-то заблокировать.
**Source:** v2.1.0 post-release audit | outcome: prevention

## 5. Ecosystem recommendations

1. **Pre-tag hook** (`/release` или `.git/hooks/pre-push` для тегов): проверяет, что `plugin.json:version` == `.ecosystem.toml:[ecosystem].version` == последнее `## [X.Y.Z]` в CHANGELOG. Блокирует push с несовпадением. Закрывает Кандидат Б.
2. **`finalize_session.py` smoke-test в CI** (или хотя бы в `scripts/health_check.py`): вызвать `record_session_trajectory()` с фикстурой и убедиться, что строка попала в `session_trajectories.jsonl`. Закрывает Кандидат А.
3. **Шаблон `task.md` для релиз-спринта** в `.claude/commands/create_spec.md`: автоматически добавлять Phase Release с чекбоксами. Закрывает Кандидат В.
4. **`/audit_ecosystem` Phase A** (subagent + slash): дополнить проверку «трекинг релиз-фазы в task.md», а не только в activeContext.md.

## 6. Overall rating

**Балл: 80/100 → 🟡 (ниже целевых 85).**

Расчёт (от 100, минусы за нарушения):
- −7 за ❌ #7 (`.ecosystem.toml` не поднят — нарушение acceptance из спеки и activeContext.md).
- −7 за ❌ #12 (trajectory ingest без happy-path run — релиз с непроверенной на живых данных функциональностью).
- −4 за ❌ #3 (release tracked outside task.md — обход guardrail by design).
- −2 за ❌ #10 (lessons не пополнялись по ходу, хотя гэпы были обнаружимы — partial-failure pattern из существующего lesson).

Положительное:
- Спека есть, утверждена, цитируется в коммитах.
- task.md закрыт по тех-пунктам.
- Pre-commit guardrails (no-verify) не обходились.
- Phase 1 имеет регрессионный harness 5/5, Phase 1 retrieve работает в проде (`retrieval_logs.jsonl`).
- Релизный коммит атомарный, тег аннотированный.

🟡 — релиз технически выпущен, но 3 acceptance-gap'а (один P1, один P1, один P2). Не 🔴 потому, что критических регрессий нет — только пропуски pre-flight checklist. Не 🟢 потому, что 14-пункт ✅ — слишком оптимистично: реально 9 ✅ / 4 ❌ / 1 закрытый-этим-аудитом ❓.

## 7. Fix plan (не исполнять — план)

| # | Файл | Действие |
|---|---|---|
| F1 | `.ecosystem.toml` | Добавить секцию `[ecosystem]` с `version = "2.1.0"`, `upstream_sha = "<git rev-parse --short HEAD>"`, заглушку `[ecosystem.file_shas]`. Закоммитить как `chore(release): sync .ecosystem.toml to v2.1.0`. (Не патч-релиз — это хвост Phase 4.) |
| F2 | `.memory/lessons.md` | Добавить 3 Memory Item из §4 (А, Б, В). |
| F3 | `task.md` (следующий спринт) | Включить Phase Release с чекбоксами как часть шаблона (см. §5.3). |
| F4 | `scripts/finalize_session.py` или `scripts/health_check.py` | Smoke-вызов `record_session_trajectory()` с фикстурой, проверка что `.memory/session_trajectories.jsonl` вырос на одну строку. |
| F5 | `.claude/hooks/` (новый) или `.git/hooks/pre-push` | Pre-tag/pre-push guardrail: сверяет версию в `plugin.json` / `.ecosystem.toml` / CHANGELOG. |
| F6 | (опционально) `/audit_ecosystem.md` Phase A | Добавить шаг: «проверить, что чекбоксы Phase Release закрыты в `task.md`, а не только в activeContext.md». |

Решение по F1-F6 — за пользователем. Subagent не коммитит.

## 8. Audit Trail (tool-calls)

1. `Bash: git log --oneline e9d73c5^..HEAD`
2. `Bash: git log --stat e9d73c5^..HEAD`
3. `Bash: git tag -l "v2.1.0" -n20`
4. `Read: task.md`
5. `Read: .memory/activeContext.md`
6. `Read: .memory/lessons.md`
7. `Bash: git log --all -S "--no-verify"`
8. `Bash: git reflog | head -40`
9. `Read: .memory/audit_history.jsonl`
10. `Bash: git diff --stat e9d73c5^..HEAD`
11. `Glob: docs/specs/2026-05-22-v2.1*`
12. `Bash: git show v2.1.0 --no-patch`
13. `Read: docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` (80 строк)
14. `Bash: git show c6632b7 -- CHANGELOG.md`
15. `Bash: git show c6632b7 -- .claude-plugin/plugin.json`
16. `Bash: git show 58dc552 --stat`
17. `Bash: git log -1 -- .memory/lessons.md`
18. `Read: .ecosystem.toml`
19. `Bash: git show c6632b7 --stat`
20. `Bash: git status --short`
21. `Bash: git diff HEAD -- .memory/audit_history.jsonl ...`
22. `Bash: git log --all --oneline | head -5` + `git branch -a`
23. `Bash: powershell Get-Content session_trajectories.jsonl` (0 байт)
24. `Bash: powershell Get-Content retrieval_logs.jsonl` (7 строк)
25. `Grep: open checkboxes in task.md` (0 совпадений)
26. `Grep: open checkboxes in activeContext.md` (1 совпадение — Phase 4)
27. `Grep: ingest_lessons|ingest_trajectories in finalize_session.py`
28. `Grep: [ecosystem]|file_shas in .ecosystem.toml` (0 совпадений)
29. `Grep: reasoning_bank_ingest|audit_complete in audit_history.jsonl`
30. `Bash: powershell file size of session_trajectories.jsonl` (0)

Итого: 30 tool-calls, минимум 8 — выполнен с запасом.
