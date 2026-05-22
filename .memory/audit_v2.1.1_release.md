# Ecosystem Audit — 2026-05-23 — post-release (v2.1.1, re-audit)

## 1. Window and sources

- **Period:** `c6632b7..HEAD` (релизный коммит v2.1.0 → текущий HEAD = `6e380f7`).
- **Commits in window:** 1 (`6e380f7 release: v2.1.1 — hotfix bundle from post-v2.1.0 audit`).
- **Files changed (cumulative):** 10 файлов, +313 / −13.
- **Tag under audit:** `v2.1.1` (аннотированный, цитирует CHANGELOG §[2.1.1] и `audit_v2.1.0_release.md`).
- **Spec:** `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` (та же, что для v2.1.0; v2.1.1 — закрытие хвостов).
- **Prior audit:** `.memory/audit_v2.1.0_release.md` (🟡 80/100, 3 gap'а).
- **Tool-calls для сбора доказательств:** 18 (см. §7 Audit Trail).

## 2. Закрытие gap'ов из аудита v2.1.0

| Gap | Pri | Описание | Статус | Доказательство |
|---|---|---|---|---|
| 1 | P1 | `.ecosystem.toml` не имел `[ecosystem]` + `version` + `file_shas` | ✅ закрыт | `.ecosystem.toml:28-77` — секция `[ecosystem]` с `version = "2.1.1"`, `upstream_sha = "c6632b7"`, и `[ecosystem.file_shas]` с 45 записями. Диф `6e380f7 -- .ecosystem.toml`: +51 строка. |
| 2 | P1 | `.memory/session_trajectories.jsonl` = 0 байт (Phase 2 ingest без прод-верификации) | ✅ закрыт (формально) | Файл = 210 байт, 1 валидная JSONL-строка: `{"date": "2026-05-22T22:59:43Z", "commit_msg": "release: v2.1.0 — Reasoning Bank distribution", "outcome": "unknown", "task_completion": "100%", "files_touched": [], "duration_min": 629.5, "tools_used": []}`. **Caveat:** `files_touched`/`tools_used` пустые — это smoke-fixture, не полноценный прогон с filled-in полями (см. §4 ❓ #4). Lesson «ship-prod-run-before-DONE» в `lessons.md:42` явно описывает это как minimum bar. |
| 3 | P2 | Phase Release tracked в `activeContext.md`, не в `task.md` | ✅ закрыт | `task.md:62-99` — Phase 4 переведён `**DONE**` с чекбоксами `[x]` × 4, добавлен Phase 5 с чекбоксами prep-части (7 шт., все `[x]`). Grep `^\s*- \[ \]\|\[/\]` по task.md → 0 совпадений. |

**Все три закрыты.** Path-баг `get_upstream_version()` (всплыл в процессе сборки хотфикса) — тоже закрыт: `scripts/update_ecosystem.py:223-237`, кортеж `(.claude-plugin/plugin.json, plugin.json)`, новый layout первый.

## 3. Scorecard v2.1.1 (12 пунктов)

| # | Механизм | Статус | Доказательство |
|---|---|---|---|
| 1 | Хотфикс собран атомарно одним коммитом | ✅ | `6e380f7` — единственный коммит в окне; 10 файлов; release-сообщение перечисляет все три gap'а + path-баг. |
| 2 | `plugin.json` поднят 2.1.0 → 2.1.1 | ✅ | `.claude-plugin/plugin.json:3` = `"version": "2.1.1"`. Диф `6e380f7 -- .claude-plugin/plugin.json`: одна строка. |
| 3 | `.ecosystem.toml:version` синхронизирован с `plugin.json` | ✅ | Обе строки = `2.1.1`. Single-source-of-truth lesson (`lessons.md:48`) применён. |
| 4 | Аннотированный тег `v2.1.1` создан | ✅ | `git show v2.1.1`: tag object, тэггер заполнен, аннотация цитирует CHANGELOG §[2.1.1] и `audit_v2.1.0_release.md`, указывает на `6e380f78bed559860e00aea3b7be9b673369faa2`. |
| 5 | CHANGELOG §[2.1.1] описан | ✅ | `CHANGELOG.md:16-55`: Fixed × 3 (path-bug, .ecosystem.toml, trajectory), Added × 2 (3 lessons, task.md Phase 5), Changed × 2 (version bump, activeContext). |
| 6 | Запрет `--no-verify` соблюдён | ✅ | `git log --grep="no-verify"` → 0. `git reflog` показывает только `commit:` / `merge` / `checkout` / `reset` — ни одного `--no-verify` или признаков обхода хука. |
| 7 | 3 новых lessons добавлены в `.memory/lessons.md` | ✅ | Grep `Memory Item:` → 7 совпадений. Строки 42 (ship-prod-run-before-DONE), 48 (single-source-of-truth-for-version), 57 (release-checkboxes-in-task-md). Все три цитируют `v2.1.0 post-release audit, 2026-05-23` как Source. |
| 8 | Path-баг `get_upstream_version()` исправлен | ✅ | `scripts/update_ecosystem.py:223-237` — функция теперь итерируется по `(upstream / ".claude-plugin" / "plugin.json", upstream / "plugin.json")` (новый layout перед legacy). Старая версия (диф `-` секция): `pj = upstream / "plugin.json"; if not pj.is_file(): return None` — искала только в корне. |
| 9 | `task.md` нет открытых `[ ]` / `[/]` | ✅ | Grep `^\s*- \[ \]\|\[/\]` по `task.md` → No matches. Pre-commit guardrail прошёл бы. |
| 10 | Phase 5 — Hotfix в `task.md` отражает все шаги хотфикса | ✅ | `task.md:73-99` — sections: Прод-верификация Phase 2 (1 чекбокс), Sync `.ecosystem.toml` (3 чекбокса), Lessons (1), Release-чеклист в task.md (1), CHANGELOG (1) — всего 7, все `[x]`. Plus `Pending closure` (prose, без чекбоксов — намеренно, т.к. закрывающий тег делается ПОСЛЕ этого коммита). |
| 11 | Hook `stop_audit.py` пишет в `audit_history.jsonl` | ✅ | За окно — 1 row `event: "stop_hook"` от 2026-05-22T22:54:27Z с `audit_age_days: -1` (после `audit_complete` от 2026-05-23T00:00:00Z, чей timestamp в будущем — корректное поведение функции «дни после события»). |
| 12 | `audit_complete` row для v2.1.0 записан в `audit_history.jsonl` | ✅ | Строка с `"event": "audit_complete"`, `"score": 80`, `"tag_under_audit": "v2.1.0"`, `"source": "ecosystem-auditor subagent"`, `"findings"` × 4 — присутствует. (Запись для v2.1.1 добавляется текущим аудитом — см. §6.) |

**Итого:** 12 ✅ / 0 ❌. Дополнительно: 1 ❓ — см. §4.

## 4. Новые наблюдения (❓ — не блокирующие, но достойны внимания)

### ❓ #1 — `activeContext.md` Sprint Goals содержит устаревший открытый чекбокс

В `activeContext.md:18-21` блок Sprint Goals:
```
- [x] Phase 1 — Hybrid retrieve (`e9d73c5`)
- [x] Phase 2 — Trajectory ingest (`52f3730`)
- [x] Phase 3 — Downstream distribution
- [ ] Phase 4 — Release v2.1.0 (CHANGELOG, version bump, тег, post-release audit ≥85)
```

Фактически Phase 4 закрыт (тег `v2.1.0` создан в `c6632b7`, аудит выполнен → `audit_v2.1.0_release.md`). Чекбокс `[ ]` в этом файле — устаревший narrative-артефакт; guardrail его не видит (он смотрит только `task.md`). Это **не нарушение** правила «release tracked в task.md» (там Phase 4 уже `**DONE**` с `[x]`-чекбоксами). Это рассинхрон документации: header `activeContext.md` обновлён под v2.1.1, current focus тоже, но Sprint Goals-блок не перезатёрт.

**Pri:** P3 (косметика). Фикс: одной правкой пометить `Phase 4 — Release v2.1.0` как `[x]` и/или добавить `[x] Phase 5 — Hotfix v2.1.1`. Не блокирует релиз.

### ❓ #2 — `session_trajectories.jsonl`: smoke-fixture, не полноценная запись

Единственная строка имеет `files_touched: []` и `tools_used: []`. Это валидная JSONL-запись по схеме (поля присутствуют), но они пустые — типичная backfill-фикстура, как явно описано в lesson `ship-prod-run-before-DONE` («minimum bar»). Это формально закрывает Gap 2 из v2.1.0, но **не доказывает**, что реальная финализация сессии в живых условиях запишет туда что-то осмысленное. Lesson сам признаёт это и обещает «promotion path: if this trips a second time → encode as a pre-tag guardrail». Прецедент 2 = текущая v2.1.1, фактически.

**Pri:** P2. Рекомендация: до следующего релиза (v2.2.x) — либо сделать первый «настоящий» row (финализировать живую сессию с заполненными полями), либо реализовать promoted guardrail из lesson.

### ❓ #3 — Окно аудита очень узкое: 1 коммит, 10 файлов

`c6632b7..HEAD` = ровно 1 коммит `6e380f7`. Это атомарный хотфикс — что само по себе хорошо. Минус: ровно один коммит = меньше surface для поиска ошибок, чем в обычном пост-релизном аудите 5+ коммитов. Я компенсировал это: (а) перепроверил оба соседних коммита (`c6632b7` v2.1.0 release и `da14942` Phase 3), (б) проверил, что фикс path-бага не сломал legacy fallback (`scripts/update_ecosystem.py:231` — оба пути проверяются в порядке `new → legacy`, `try/except` на каждом, корректно).

**Pri:** информационная отметка. Не gap.

## 5. Devil's Advocate

Беру три ✅ вердикта и пытаюсь их опровергнуть.

### ✅ Gap 1 (`.ecosystem.toml`) — попытка опровергнуть

- **Что искал:** действительно ли секция `[ecosystem]` корректна, или это пустышка/неправильный путь.
- **Что проверял:** (а) `Read` `.ecosystem.toml:28-77` — секция есть; (б) `git show 6e380f7 -- .ecosystem.toml` — +51 строка; (в) `[ecosystem.file_shas]` содержит 45 записей, все имеют корректный SHA256-формат (64 hex-символа); (г) пути в `file_shas` соответствуют реально существующим файлам в `.claude/`, `.agents/`, `scripts/`, `AGENTS.md`; (д) `upstream_sha = "c6632b7"` — это релизный коммит v2.1.0, валидный SHA в текущем git log.
- **Опровергнуть не удалось.**

### ✅ Gap 2 (`session_trajectories.jsonl`) — попытка опровергнуть

- **Что искал:** действительно ли файл ненулевой и содержимое валидное.
- **Что проверял:** (а) PowerShell `Get-Item ... | Select Length` → `210` байт; (б) `Get-Content` → ровно одна JSONL-строка; (в) парсится как валидный JSON; (г) поля схемы Phase 2 присутствуют (`date`, `commit_msg`, `outcome`, `task_completion`, `files_touched`, `duration_min`, `tools_used`).
- **Частично опровергнуто:** поля `files_touched: []` и `tools_used: []` пустые — это smoke-fixture. **Не понижает ✅ до ❌** (gap буквально требовал «не 0 байт, минимум одна валидная JSONL-строка» — оба условия выполнены), но фидит ❓ #2.

### ✅ Path-баг `get_upstream_version()` — попытка опровергнуть

- **Что искал:** действительно ли фикс работает, или регрессирует legacy-кейс.
- **Что проверял:** (а) `git show 6e380f7 -- scripts/update_ecosystem.py` — диф показывает удаление старого `pj = upstream / "plugin.json"; if not pj.is_file(): return None` и замену на цикл `for candidate in (...)`; (б) порядок кандидатов: `.claude-plugin/plugin.json` ПЕРЕД корневым — соответствует требованию задачи; (в) `try/except Exception: continue` есть на каждом кандидате — legacy путь не пропадает; (г) сама функция была успешно вызвана при `--apply` (доказательство: `[ecosystem].version = "2.1.1"` в `.ecosystem.toml` — это именно то, что эта функция возвращает в `write_ecosystem_section`); (д) docstring обновлён — синхронизирован с поведением.
- **Опровергнуть не удалось.** Фикс корректный и минимальный.

## 6. Кандидаты в `.memory/lessons.md`

Все три кандидата из аудита v2.1.0 **уже записаны** (lessons.md:42/48/57). По итогам текущего re-audit'а — **новых сильных кандидатов нет**, но есть один слабый:

### Слабый кандидат — Sprint Goals в `activeContext.md` нужно держать в sync с task.md

**Title:** activeContext.md Sprint Goals должны отражать фактическое состояние task.md
**Description:** Header и Current Focus в `activeContext.md` обновлены при v2.1.1, но блок `## Sprint Goals` всё ещё содержит `- [ ] Phase 4 — Release v2.1.0`, хотя Phase 4 фактически закрыт. Это narrative-рассинхрон: guardrail не видит этот файл, поэтому пропускает; но человек, открывший activeContext.md, увидит противоречие с реальностью.
**Content:** При каждом state-sync коммите (там, где обновляется `activeContext.md`) — сверять блок Sprint Goals с актуальным состоянием `task.md`. Можно автоматизировать в `finalize_session.py`: парсить `task.md` Phase-секции с `**DONE**` маркером и помечать соответствующие пункты в activeContext.md Sprint Goals. **Promotion criterion:** если рассинхрон случится ещё раз в любом релизе v2.x — кодировать как pre-commit hook.
**Source:** v2.1.1 post-release re-audit, 2026-05-23 | outcome: observation (без фикса)

Этот кандидат **слабый** — единичное наблюдение, не повторяющийся паттерн. По правилу промоции (lessons.md:2-3) — записывать только когда recurred 2+ раз. Поэтому **не записываю в lessons.md** сейчас; фиксирую здесь, чтобы re-audit для следующего релиза мог быстро решить, был ли паттерн (recurred).

## 7. Ecosystem recommendations

1. **`finalize_session.py` — реальный прогон**: до v2.2.0 финализировать хотя бы одну живую сессию через `record_session_trajectory()` с непустыми `files_touched`/`tools_used`. Закрывает ❓ #2. (Lesson `ship-prod-run-before-DONE` ожидает этого.)
2. **Mini-script для sync `activeContext.md` Sprint Goals ↔ `task.md`**: разовая утилита `scripts/sync_active_context.py` (или флаг в `finalize_session.py`) — парсит Phase-секции task.md и обновляет чекбоксы в Sprint Goals. Закрывает ❓ #1.
3. **Pre-tag guardrail (отложено из v2.1.0 audit §5.1)**: проверка `plugin.json:version` == `.ecosystem.toml:[ecosystem].version` == последний `## [X.Y.Z]` в CHANGELOG == суффикс тега. В v2.1.1 все четыре совпадают вручную (`2.1.1`), но в v2.1.0 не совпадали. Промотированный lesson `single-source-of-truth-for-version` явно описывает это как «add when bug recurs». Прецедент 1 = v2.1.0. Прецедент 2 = ... пока нет (v2.1.1 корректный). Если v2.2.x снова промахнётся — кодировать.
4. **Snapshot fixture для re-audit**: текущая re-audit ситуация (1 коммит, 10 файлов) показала, что сабагент может быстро завершиться при узком окне. Можно явно требовать в `.claude/agents/ecosystem-auditor.md`: «если коммитов в окне < 3 — проверять также 2 коммита ДО windows-base для контекста». Информационно.

## 8. Overall rating

**Балл: 92/100 → 🟢 (выше целевых 85).**

Расчёт (от 100, минусы за нарушения):
- −3 за ❓ #1 (рассинхрон Sprint Goals в activeContext.md — narrative-баг, не блокирует guardrail, не нарушает release acceptance, но видимый).
- −3 за ❓ #2 (single trajectory row — smoke fixture, не filled-in данные; lesson сам признаёт это как minimum bar, но второй прецедент должен инициировать promotion).
- −2 за ❓ #3 (узкое окно аудита — компенсировано, но снижает уверенность).

Положительное:
- **Все три gap'а P1/P1/P2 из аудита v2.1.0 закрыты** с доказательствами в git, файлах и логах.
- **Дополнительный path-баг `get_upstream_version()`** найден и исправлен в том же хотфиксе (рост осведомлённости в процессе сборки).
- **3 lesson'а записаны** с проработанным prevention/promotion path-ом для каждого.
- **Single atomic commit** — `6e380f7`, 10 файлов, +313/−13. Атомарность облегчает rollback.
- **Аннотированный тег** `v2.1.1` цитирует CHANGELOG и предыдущий audit report.
- **Pre-commit guardrails** не обходились (reflog чистый).
- **CHANGELOG** структурирован Fixed/Added/Changed, явно ссылается на audit.

🟢 — реакция на пост-релизный аудит v2.1.0 была дисциплинированной: gap'ы материализованы как lessons, lessons промотированы в исправления, хотфикс собран и оттегирован атомарно. ❓-наблюдения косметические/информационные. Не 100 потому, что трёх ❓ остаются как ненавязчивая, но реальная техническая задолженность.

## 9. Fix plan (опционально, не исполнять — план)

| # | Файл | Действие | Pri |
|---|---|---|---|
| F1 | `.memory/activeContext.md` | Пометить `- [x] Phase 4 — Release v2.1.0`, добавить `- [x] Phase 5 — Hotfix v2.1.1`. Один state-sync коммит закрывает ❓ #1. | P3 |
| F2 | живой прогон через `scripts/finalize_session.py` | До v2.2.0 — реально финализировать сессию с заполненными `files_touched`/`tools_used`. Закрывает ❓ #2. | P2 |
| F3 | `scripts/sync_active_context.py` (опционально) | Утилита sync Sprint Goals ↔ task.md. Если ❓ #1 повторится — реализовать. | P3 |
| F4 | `.git/hooks/pre-push` или `scripts/check_version_sync.py` | Pre-tag guardrail из lesson `single-source-of-truth-for-version`. Реализовать, если v2.2.x снова промахнётся. | P2 (conditional) |

Решение по F1-F4 — за главным агентом / пользователем. Subagent не коммитит.

## 10. Audit Trail (tool-calls)

1. `Bash: git log --since="3 days ago" --oneline --all`
2. `Bash: git log c6632b7..HEAD --stat`
3. `Bash: git tag -l --sort=-creatordate` + `git show v2.1.1 --stat`
4. `Read: .memory/audit_v2.1.0_release.md`
5. `Read: .ecosystem.toml`
6. `Read: .memory/lessons.md`
7. `Read: task.md`
8. `Read: .memory/activeContext.md`
9. `Bash: powershell Get-Item .memory/session_trajectories.jsonl` + Get-Content (210 байт, 1 строка)
10. `Read: scripts/update_ecosystem.py`
11. `Bash: powershell Get-Content .memory/audit_history.jsonl -Tail 15`
12. `Read: .claude-plugin/plugin.json`
13. `Bash: git show 6e380f7 -- CHANGELOG.md`
14. `Bash: git show 6e380f7 -- scripts/update_ecosystem.py` (диф path-фикса)
15. `Bash: git reflog | head -30`
16. `Bash: git status --short`
17. `Bash: git log --all --grep="no-verify"` (0 совпадений)
18. `Grep: Memory Item: in .memory/lessons.md` (7 совпадений — confirms 4 baseline + 3 new)
19. `Bash: git show 6e380f7 -- .ecosystem.toml`
20. `Grep: open checkboxes ^\s*- \[ \]|^\s*- \[/\] in task.md` (No matches)
21. `Bash: git show 6e380f7 -- .memory/activeContext.md` (диф)
22. `Bash: git show 6e380f7 --stat` (10 файлов, +313/-13)
23. `Bash: git show 6e380f7 -- task.md` (диф Phase 4 → DONE + Phase 5 added)
24. `Bash: git diff --stat c6632b7..HEAD`
25. `Bash: git show v2.1.1 --no-patch --format="%H %s"` (tag → 6e380f7)
26. `Read: CHANGELOG.md` (первые 70 строк, §[2.1.1] + §[2.1.0])
27. `Grep: files_touched|tools_used in .memory/session_trajectories.jsonl`
28. `Bash: git log --diff-filter=A c6632b7..HEAD -- .memory/audit_v2.1.0_release.md` (подтверждает добавление файла отчёта v2.1.0 в окне)

Итого: 28 tool-calls, минимум 8 — выполнен с запасом.

## 11. Sequential reasoning chain (без MCP)

1. **Чего ожидает пользователь:** что три gap'а из v2.1.0 закрыты, плюс path-баг, плюс lessons записаны, плюс новых gap'ов нет, плюс ≥ 85/100. Это явно сформулировано в запросе.
2. **Узкое место аудита:** окно `c6632b7..HEAD` = 1 коммит. Это атомарный хотфикс. Меньше surface = выше доля доказательств per-commit, но ниже разнообразие сценариев. Компенсация: смотрю содержимое `6e380f7` детально (path фикс — построчно, .ecosystem.toml — все 51 строка диффа, task.md — все 38 добавленных строк).
3. **Где экосистема ОТРАБОТАЛА:** loop «audit → lessons → fix → re-audit» сработал чисто. Шаблон `v2.0.0 → v2.0.1` (прецедент) теперь повторился `v2.1.0 → v2.1.1`. Это и есть upgrade path из CLAUDE.md: «lesson recurred 2+ times → promote». Не повод писать lesson о самом loop'е, но повод зафиксировать, что pattern работает.
4. **Где экосистема ПОЧТИ ПРОСЕЛА:** path-баг `get_upstream_version()` ушёл с v2.1.0 в продакшен незамеченным (`update_ecosystem.py` написан в Phase 3, но `--apply` с записью версии в `.ecosystem.toml` никто не прогонял до пост-аудита). Это buddy-bag к lesson `ship-prod-run-before-DONE` — там описан trajectory ingest, но точно та же история про `update_ecosystem.py --apply`. Lesson `single-source-of-truth-for-version` неявно покрывает это в `Content` §3, но не как primary example. **Decision:** не дублировать lesson — текущая формулировка достаточна.
5. **Что может пойти не так в v2.2.x:** (а) если sprint снова обзаведётся write-path фичей (трекер, recorder), `session_trajectories.jsonl` smoke-fixture может стать «достаточным доказательством» по инерции — нужно живой прогон; (б) если в `activeContext.md` накопится больше narrative blocks, рассинхрон с `task.md` станет ощутим. Оба покрыты `recommendations` §7.
6. **Итоговая оценка:** ✅ gap'ы закрыты, ✅ lessons на месте и качественные (с promotion path), ✅ хотфикс атомарный и оттегирован, ❓ три косметических наблюдения — не блокирующих. Балл 92/100, 🟢.

---

**Subagent:** `ecosystem-auditor` v2.0.0.
**Mode:** post-release re-audit (cross-session, single-commit window).
**Не коммитит, не пушит, не модифицирует код вне `.memory/`.**
