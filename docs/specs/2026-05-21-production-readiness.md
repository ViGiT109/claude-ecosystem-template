# Spec: Production-Readiness Upgrade — v1.0 → v2.0.0

**Status:** Approved (2026-05-21)
**Plan reference:** `~/.claude/plans/parallel-leaping-rainbow.md` (local working copy)
**Audit reference:** Conversation 2026-05-21 — maturity score 82/100

---

## Problem statement

Текущий шаблон `claude-ecosystem-template` v1.0 архитектурно сильный (ReasoningBank, 3-tier memory, deterministic hooks, self-improving loop), но имеет три критических дефекта блокирующих массовое клонирование и отстаёт в дистрибуции от стандарта 2026:

1. **`.claude/Skills/` с заглавной буквы** — на macOS/Linux сломается (case-sensitive FS).
2. **`plugin.json` рассинхронизирован с реальностью** — невозможно публиковать как плагин.
3. **Нет AGENTS.md** — несовместимо с другими AI-инструментами (Cursor, Windsurf, Codex CLI).

Дополнительно пользователь запросил два сквозных механизма:
- **Уведомление о моменте глубокого планирования** (детерминированное)
- **Рекомендация модели Opus 4.7 / Sonnet 4.6** (системная политика выбора)

## Scope

### In scope
- 6 фаз → 6 PR
- Создание AGENTS.md как source-of-truth с pre-commit-стражем
- Model Routing System с явным frontmatter в каждой команде/агенте
- Planning Phase Detector (UserPromptSubmit hook на RU+EN)
- Автогенерация plugin.json + pre-publish marketplace.json
- Авто-ингест ReasoningBank в finalize_session.py
- Новые субагенты: code-reviewer, researcher
- Cleanup: удаление дублей, переименование frozen snapshot

### Out of scope (v2.1+)
- Hybrid search (BM25 + vector) в reasoning_bank.py
- Сравнительный документ с Superpowers / Spec Kit
- CI matrix builds (macOS/Linux runners)
- Финансовые/security субагенты
- Локализация документации
- Публикация в Anthropic plugin marketplace (после стабилизации)

## Architectural decisions (17 confirmed forks)

| # | Решение | Выбор |
|---|---|---|
| 1 | Default model | Opus 4.7 by default, Sonnet 4.6 only on explicit safe-path triggers |
| 1a | **Context Window Awareness** | Учитывается во всех рекомендациях: Opus 4.7 = 1M ctx, Sonnet 4.6 = 200K ctx. Recommend new session при >70% заполнения; recommend Opus when task needs >150K ctx irrespective of complexity |
| 1b | **Model Switch Checkpoint** (минимально-блокирующий) | Тормозу с blocking `💡 MODEL` блоком **только** когда: (a) текущая модель не подходит для предстоящей задачи И (b) делегирование на subagent невозможно. Если можно решить через subagent — делаю молча. Если текущая модель справится без потерь — не упоминаю переключение. |
| 1c | **Hybrid via subagents (silent)** | При вызове `Agent` всегда явно указываю `model:`. Делегирование на subagent выполняется **без уведомления пользователя и без торможения** — это внутренняя оптимизация. Главный поток продолжается, пользователю показывается только итоговый результат. |
| 1d | **Default start model** | Новые сессии стартуют на **Opus 4.7** (надёжность приоритет). Sonnet — opt-in через явное `/model claude-sonnet-4-6` от пользователя. |
| 2 | Planning detector | Двухслойный: UserPromptSubmit hook + AGENTS.md rule |
| 3 | AGENTS.md / CLAUDE.md | AGENTS.md source-of-truth; CLAUDE.md — генерируемая копия |
| 4 | Built-in skills | Только clean-workspace + deploy-fresh; deep-research/triz/problem-solving удалить |
| 5 | `/extract_lesson` model | Opus 4.7 |
| 6 | `/model_check` command | Создаём |
| 7 | Trigger langs | RU + EN |
| 8 | Hint format | Единый блок 🧭 PLAN + 💡 MODEL + env-killswitch |
| 9 | claude_code_state.md | Переименовать в api_reference_hooks.md |
| 10 | Новые субагенты | Оба: code-reviewer (Opus) + researcher (Sonnet) |
| 11 | Statusline | Минимальный встроенный (model + branch + tokens) |
| 12 | plugin.json sync | Auto-regenerate + pre-commit check |
| 13 | Marketplace | Pre-publish prep — файл есть, не публикуем |
| 14 | Version | v2.0.0 (major; breaking changes) |
| 15 | pyproject.toml | Скаффолдить в bootstrap.ps1 при language=python |
| 16 | Strategy | 1 PR на фазу = 6 PR |

## Proposed solution — 6 фаз

### Phase 1: Critical fixes → PR #1 (Sonnet 4.6, ~2ч)
- 1.1. `.claude/Skills/` → `.claude/skills/` (двухходовка через temp)
- 1.2. Удалить `deep-research/`, `triz/`, `problem-solving/`
- 1.3. `session_start.py`: блок `🔴 BOOTSTRAP REQUIRED` при необработанных placeholder'ах
- 1.4. `AGENTS.md` (новый) + `scripts/sync_agents_md.py` + pre-commit hook `agents-md-sync`

### Phase 2: Distribution-readiness → PR #2 (Sonnet 4.6, ~3ч)
- 2.1. `scripts/regenerate_plugin_manifest.py` + pre-commit `--check`
- 2.2. `.claude-plugin/marketplace.json` (валидный, не публикуем)
- 2.3. `session_start.py`: проверка свежести audit_history.jsonl (>14 дней → 🟡)

### Phase 3: Model Routing System → PR #3 (Opus для [3.1], Sonnet для остального, ~3.5ч)
- 3.1. `.agents/rules/model-policy.md` (~120–150 строк, с разделом Context Window Awareness) — Opus
- 3.2. Frontmatter `model:` в 8 командах (см. таблицу в плане)
- 3.3. `ecosystem-auditor.md`: `model: inherit → opus`
- 3.4. `/model_check` slash-command (включая context window в output)
- 3.5. `/handoff` slash-command — подготовка к новой сессии

### Phase 4: Planning Phase Detector + Context Monitor → PR #4 (Opus для [4.0]+[4.1], Sonnet для остального, ~3ч)
- 4.0. Context window monitor в `session_start.py` — рекомендация `🔄 NEW SESSION` при >70% ctx
- 4.1. `.claude/hooks/planning_hint.py` + regex RU/EN + env killswitch — Opus
- 4.2. AGENTS.md: секции «Planning-phase signaling» + «Session handoff signaling»
- 4.3. Cross-reference в `model-policy.md`

### Phase 5: ReasoningBank automation → PR #5 (Sonnet 4.6, ~1ч)
- 5.1. Патч `finalize_session.py` после line 172 — non-blocking subprocess ingest_lessons

### Phase 6: Cleanup & enrichment → PR #6 (Opus для [6.2], Sonnet для остального, ~3.5ч)
- 6.1. Cleanup: rm `monitor_context.sh`, переименовать `claude_code_state.md` → `api_reference_hooks.md`
- 6.2. Новые субагенты `code-reviewer.md` (Opus) + `researcher.md` (Sonnet) — Opus дизайн
- 6.3. Statusline: `.claude/hooks/statusline.py` + регистрация в settings.json
- 6.4. `outputStyle: default` в settings.json
- 6.5. `pyproject.toml` скаффолдинг в bootstrap.ps1
- 6.6. Примеры в `docs/adr/` и `docs/specs/`
- 6.7. `docs/template-design.md` (поглощает TEMPLATE_README.md)
- 6.8. `.env.example` обогащение (ANTHROPIC_API_KEY, HTTPS_PROXY, CLAUDE_DISABLE_PLANNING_HINT)

## Acceptance criteria (release v2.0.0)

1. ✅ Клонирование на macOS/Linux работает (lowercase `.claude/skills/`)
2. ✅ `bootstrap.ps1` на свежей VM генерирует pyproject.toml при language=python и удаляет placeholder'ы
3. ✅ Pre-commit hooks: `agents-md-sync` + `plugin-manifest-sync` + `task-guardrail` блокируют drift
4. ✅ `planning_hint.py` срабатывает на RU+EN триггерах; env killswitch работает
5. ✅ Каждая slash-команда и субагент имеют явный `model:` в frontmatter
6. ✅ `/model_check` возвращает блок 💡 MODEL
7. ✅ Финализация сессии триггерит ReasoningBank ingest; статус в audit_history.jsonl
8. ✅ Statusline отображает модель + branch + token usage
9. ✅ `marketplace.json` валиден (json.load без ошибок)
10. ✅ CHANGELOG.md содержит секцию BREAKING CHANGES v2.0.0
11. ✅ Git tag v2.0.0

## Verification strategy

Каждый PR заканчивается smoke-тестами (детали в плане).
Финальная end-to-end проверка:
- `git clone` на macOS/Linux → `ls .claude/skills` → присутствует
- `bootstrap.ps1` на Windows → `/new_session` без placeholder'ов
- Test prompt «рефактор модуля X» → детектор срабатывает, единый блок выводится

## Risks & mitigations

| Риск | Митигация |
|---|---|
| AGENTS.md ↔ CLAUDE.md рассинхрон | pre-commit `agents-md-sync` блокирует commit |
| Регрессия plugin.json при добавлении файлов | pre-commit `plugin-manifest-sync` с `--check` |
| Hook hang на больших prompt'ах | timeout 3s в settings.json, killswitch CLAUDE_DISABLE_PLANNING_HINT=1 |
| Ложные срабатывания planning detector | Whitelist коротких prompt'ов (<20 символов) — добавить в hook |
| ChromaDB ingest падает в Phase 5 | `check=False` + log status, не блокирует finalize_session.py |
| Statusline ломает TUI | Pure Python, без внешних зависимостей; timeout 1s |

## Estimated effort

- **Sonnet 4.6 (~70%):** ~8ч (фазы 1, 2, 5 целиком + реализация 3, 4, 6)
- **Opus 4.7 (~30%):** ~3ч (дизайн model-policy, planning hook regex, новые субагенты)
- **Итого:** ~11ч чистого времени работы

## References

- Audit report: in-conversation 2026-05-21
- ReasoningBank paper: https://arxiv.org/pdf/2509.25140
- AGENTS.md standard: https://github.com/openai/codex/blob/main/AGENTS.md (де-факто 2026)
- Claude Code marketplace docs: https://code.claude.com/docs/en/plugin-marketplaces
- Plan file (working copy): `C:\Users\vibev\.claude\plans\parallel-leaping-rainbow.md`
