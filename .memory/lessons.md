# Журнал ошибок — извлечённые уроки

> **Self-Improvement Loop:** этот файл автоматически читается в начале каждой сессии через `/new_session`.
> Агент обязан учитывать эти уроки и не повторять задокументированные ошибки.
> Чтобы добавить новый урок — используй workflow `/extract_lesson`.

> **Формат (ReasoningBank v1):** каждый урок — структурированный Memory Item.
> Структура: Title / Description / Content / Source (поля имеют английские имена,
> потому что их парсит `scripts/reasoning_bank.py::parse_lessons()` по regex).

---

## Кросс-проектные (универсальные)

### Memory Item: Never read large files in full
**Title:** Large file reading prevention
**Description:** Лог-файлы и runtime-данные могут весить мегабайты — всегда читай только хвост.
**Content:** Используй `Get-Content -Tail 100/200` (PowerShell) или `tail -n 200` (POSIX). Чтение большого runtime-файла целиком вызывает переполнение контекста и потерю рабочей памяти.
**Source:** template baseline | outcome: prevention

### Memory Item: Close tasks in task.md continuously
**Title:** Continuous task.md completion
**Description:** Дрейф промпта во время долгих операций приводит к брошенным задачам.
**Content:** В длинных сессиях агент склонен забывать обновлять `task.md`, оставляя пункты `[ ]` / `[/]`. Pre-commit guardrail блокирует коммит при наличии незакрытых задач. Помечай каждый шаг `[x]` сразу после завершения — а не в конце сессии.
**Source:** template baseline | outcome: prevention

---

## Проектные

### Memory Item: Append-only logs need event-type filters for "freshness" checks
**Title:** Don't measure freshness by mtime or last-line on a write-heavy log
**Description:** Сигнал свежести/застаревания для append-only JSONL-лога бессмысленен, если файл пишется высокочастотным событием (например, каждый ход Claude). Использование mtime файла или `lines[-1]` маскирует реальный возраст сигнала, который интересен пользователю.
**Content:** `.memory/audit_history.jsonl` дописывается из `stop_audit.py` на каждый Stop-хук (`event: "stop_hook"`) — раз за ход Claude. Исходные `audit_age_days()` (в `stop_audit.py`) и `check_audit_debt()` (в `finalize_session.py`) докладывали возраст **последней записи** или **mtime файла** — оба значения всегда были «секунды назад». Итог: сигнал «не было полного аудита за N дней» никогда не мог сработать. **Фикс:** всегда фильтруй по конкретному типу `event`, который тебя интересует (`event == "audit_complete"`), и ищи самую свежую квалифицирующую запись; никогда не используй mtime файла как прокси для «случилось ли это конкретное событие недавно». Продюсеры таких событий обязаны эмиттировать их явно — `/audit_ecosystem` Phase E теперь добавляет маркер `audit_complete`.
**Source:** Phase 2 PR #2, 2026-05-21 | outcome: prevention + fix applied

### Memory Item: Don't outsource contextual signals to deterministic hooks
**Title:** Emit PLAN/MODEL block manually when triggers are contextual, not lexical
**Description:** `planning_hint.py` (UserPromptSubmit) срабатывает только на ключевые слова RU/EN или ≥3 ссылки на файлы — by design. Когда промпт пользователя короткий («делаем всё по порядку», «продолжаем», «действуй»), но фактическая работа архитектурная (написание многофазной спецификации, проектирование подсистемы, объём релиза), хук молчит. AGENTS.md явно требует, чтобы агент закрывал этот gap вручную; полагаться только на хук — это тихий дрейф от планировочной/модельной политики.
**Content:** **Root cause:** агент воспринимает `planning_hint.py` как полный детектор планирования, а не как первую (лексическую) линию обороны. **Prevention:** перед вызовом `/create_spec`, `/agentic_tdd` или любого design-скилла — и перед любой работой, которая охватывает >1 фазы или >3 файлов — проверь, был ли эмиттирован `🧭 PLAN + 💡 MODEL` блок (хуком ранее в ходу, или мной inline). Если нет — эмиттируй его перед вызовом скилла. Формат блока — в `.agents/rules/model-policy.md` §Block formats. Стоимость лишнего блока почти нулевая; стоимость пропущенного — дрейф политики, который пользователь должен ловить сам.
**Source:** session 2026-05-22 (создание спецификации v2.1) | outcome: partial-failure (спецификация написана корректно, но сигнальный блок пропущен)

### Memory Item: Reply in user's language regardless of code-context language
**Title:** Mirror prompt language, not codebase language
**Description:** Пользователь пишет по-русски и ждёт ответов по-русски. При погружении в технический контент (код, спецификации, лог-выводы — всё на английском) агент дрейфует и начинает зеркалить язык контекста, а не язык собеседника. Это раздражает и ломает рабочий процесс — пользователю приходится повторно поправлять.
**Content:** **Root cause:** агент дисциплинированно держится русского в первых нескольких ответах, но по мере погружения в long-running технический контекст переключается на английский (модель зеркалит окружение). **Prevention:** язык user-facing текста (сообщения, end-of-turn summaries, обновления о ходе работы) определяется языком **последнего сообщения пользователя**, а не контекстом задачи. Технический контент в файлах (имена переменных, frontmatter, Conventional Commits, артефакты-шаблоны) — остаётся английским, если стиль файла английский. **Guardrail:** хук `.claude/hooks/language_check.py` (UserPromptSubmit) детектирует кириллицу в промпте и инжектит напоминание отвечать по-русски — закрывает дыру детерминистически, так же как `block_no_verify.py` закрыл `--no-verify`.
**Source:** session 2026-05-22 (повторяющаяся жалоба пользователя на дрейф на английский) | outcome: prevention + fix applied (hook + i18n)

---

## Анти-паттерны

<!-- Паттерны, повторявшиеся 3+ раз и ставшие жёсткими правилами -->
<!-- Также добавляй в .agents/rules/ при промоушене анти-паттерна в правило -->
