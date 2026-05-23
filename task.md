# Task: v2.2 Self-Diagnostic Ecosystem

**Spec:** [docs/specs/2026-05-23-v2.2-self-diagnostic-ecosystem.md](docs/specs/2026-05-23-v2.2-self-diagnostic-ecosystem.md)
**Plan:** `~/.claude/plans/magical-drifting-reddy.md` (approved)
**Sprint progress:** tracked in [.memory/activeContext.md](.memory/activeContext.md)

> **Tracking convention:** только текущая фаза держит `- [x]` чекбоксы.
> Будущие фазы — bullet'ы без `[ ]`/`[x]`, чтобы pre-commit guardrail
> не блокировал промежуточные коммиты. Когда фаза начинается — её
> bullet'ы превращаются в `- [x]` (закрытие = последний шаг фазы).

## Phase 1 — Pre-push version-sync guardrail (Layer A) — **DONE**

- [x] `scripts/check_version_sync.py` — проверяет `plugin.json::version` ↔ CHANGELOG `## [X.Y.Z]` ↔ push'имые теги ↔ `.ecosystem.toml::ecosystem.version`
- [x] Регистрация в `.pre-commit-config.yaml` (новый блок `check-version-sync`, `stages: [pre-push]`)
- [x] Документация: `setup_environment.md`, `ENVIRONMENT_SETUP.md`, `deploy-fresh/SKILL.md` — добавлен вызов `pre-commit install --hook-type pre-push`
- [x] Pre-push hook установлен локально (`.git/hooks/pre-push`)
- [x] Unit-тесты: drift detection (plugin.json=9.9.9) → exit 1; restore → exit 0; pre-push stdin (4 кейса: wrong tag, correct tag, branch, deletion) — все корректны

## Phase 2 — Hook health-check (Layer A + B) — **DONE**

- [x] `scripts/check_hook_health.py` — парсит `.claude/settings.json::hooks`, для каждого хука: проверяет существование файла, запускает с `HOOK_DRYRUN=1` + пустым JSON stdin, проверяет exit 0
- [x] Dry-run mode (`HOOK_DRYRUN=1`) добавлен во все 4 хука: `session_start.py`, `stop_audit.py`, `planning_hint.py`, `block_no_verify.py` — early-return после imports
- [x] Пишет `{"event": "hook_health_check", "status": "ok"|"degraded", "checked": N, "failed_hooks": [...]}` в `.memory/audit_history.jsonl`
- [x] Новый раздел «Hooks» в `scripts/health_check.py` — вызывает `check_hook_health.py`, прокидывает результат в overall pass/fail
- [x] Unit-тест: инжект SyntaxError в `planning_hint.py` → exit 1 с тэйлом ошибки в `failed_hooks[].detail`; restore → exit 0; обе попытки записаны в `audit_history.jsonl`

## Phase 3 — Auto-audit trigger в session_start.py (Layer B) — **DONE**

- [x] `.claude/hooks/_ecosystem_health.py` — общий stdlib-only модуль: `audit_age_days`, `stop_hook_count_since_audit`, `last_audit_info`, `consolidate_age_days`, `hook_health_age_hours`, `lessons_count`; combined verdict helpers `audit_status` / `consolidate_status` / `hook_health_status`; пороги (AUDIT_REQUIRED_DAYS=7, AUDIT_AGING_DAYS=3, AUDIT_REQUIRED_STOP_HOOKS=20, …) — единый источник правды
- [x] `stop_audit.py` импортирует `audit_age_days` из `_ecosystem_health` (sys.path тюнинг для sibling import); локальная копия удалена
- [x] `emit_audit_freshness()` переписан на `audit_status()` — три состояния: 🔴 `AUDIT REQUIRED` (age≥7 OR stop_hook_count≥20) + window-hint из `last_audit_info().tag_under_audit`; 🟡 `audit aging` (3-7 дней); silent (<3 дней)
- [x] Unit-тесты (подмена timestamp в audit_history.jsonl): 13 дней назад → 🔴 + window `v2.0.0..HEAD`; 4 дня назад → 🟡 «audit aging — last audit 4 day(s) ago»; current → silent; stop_audit.py end-to-end не сломан

## Phase 4 — Consolidate-memory trigger (Layer B) — **DONE**

- [x] `emit_consolidate_freshness()` в `session_start.py` (симметрично emit_audit_freshness, использует `_eh.consolidate_status()`)
- [x] `.claude/commands/consolidate_lessons.md` — slash-команда, инструктирует агента вызвать `anthropic-skills:consolidate-memory` и после успеха записать `consolidate_complete` event в `.memory/audit_history.jsonl`
- [x] Триггер: age ≥ 30 дней OR `lessons_count() >= 20` → 🟡 `CONSOLIDATE RECOMMENDED`; иначе silent
- [x] Unit-тесты: 7 лессонов + no consolidate_complete → silent (ниже порога); инжект 20 fake lesson'ов → 🟡 «27 lesson(s), never consolidated»; restore → silent

## Phase 5 — Diagnostic dashboard + `/diag_status` (Layer C) — **DONE**

- [x] `scripts/diag_dashboard.py` — 6 секций: Audits (last + trend + sessions-since), Lessons (count + consolidate status), Retrieval mix (mode % + collections), Trajectories (outcomes + avg duration), Hooks (status + last check details), Version sync (3 источника + last tag); все используют общий `_ecosystem_health` модуль
- [x] `--summary` флаг → 4 строки светофора (audit / lessons / hooks / version)
- [x] `.claude/commands/diag_status.md` — slash-команда, вызывает дашборд `--summary` и предлагает actions для каждого не-зелёного индикатора
- [x] Unit-тест: текущее состояние — полный отчёт без падения, summary показывает 🟢 везде

## Phase 6 — Ecosystem health injection в session_start.py (Layer C) — **DONE**

- [x] Новый блок `## 📊 Ecosystem health` в инжекте — 4 индикатора (audit / lessons / hooks / version sync), всегда печатается, мирорит `diag_dashboard.py --summary`
- [x] Старый `emit_lessons_freshness()` удалён — lessons-сигнал теперь часть unified block через `consolidate_status()` (strictly more informative)
- [x] Action-блоки (🔴 AUDIT REQUIRED / 🟡 CONSOLIDATE RECOMMENDED) остались отдельно ВЫШЕ summary — урgent action видим первым; summary даёт at-a-glance статус
- [x] Светофор-логика и version-sync чтение — из `_ecosystem_health` модуля + stdlib (json/re для plugin.json + CHANGELOG)
- [x] Unit-тест: новая сессия → блок виден в инжекте, все 4 индикатора 🟢, версии 2.1.1 совпадают

## Phase 7 — Release v2.2.0 (prep) — **DONE**

### Prep
- [x] Bump `.claude-plugin/plugin.json::version` 2.1.1 → 2.2.0
- [x] `python scripts/update_ecosystem.py --from . --apply` — синк `.ecosystem.toml::ecosystem.version` (51 unchanged, секция [ecosystem] обновлена с version=2.2.0)
- [x] CHANGELOG §[2.2.0] — описаны все 6 фаз с Layer A/B/C группировкой + Added/Changed/Fixed
- [x] Standalone check_version_sync.py: ✅ versions in sync (plugin.json=CHANGELOG=.ecosystem.toml=2.2.0)

### Pending closure (отдельный state-sync коммит ПОСЛЕ тега и аудита)

- Self-test: temp-тег v9.9.9 → push блокирован pre-push guardrail → удалить
- Аннотированный тег v2.2.0 + push --follow-tags (свой pre-push guardrail должен пройти)
- Post-release audit сабагентом → ≥ 85/100 (иначе хотфикс v2.2.1)
- activeContext.md синхронизирован, Sprint Goals [x]
