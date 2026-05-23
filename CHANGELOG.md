# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

<!-- Add changes here as they are made -->

---

## [2.3.0] — 2026-05-23

Closes the loose ends carried over from v2.2: lesson → rule promotion path
made deterministic, real per-session tool-usage telemetry, and an automated
recurrence detector that surfaces unpromoted lessons before the next audit
does. No backwards-incompatible changes — all additions are additive.

### Added

- **Pre-commit guardrail for activeContext.md Sprint Goals desync**
  (`scripts/check_activectx_sprint_goals.py`, registered in
  `.pre-commit-config.yaml`). Fires only when the `version` field of
  `.claude-plugin/plugin.json` changes in the staged diff (release-bump
  heuristic) and blocks the commit if any `- [ ]` / `- [/]` checkbox remains
  under a `## Sprint Goals` heading. Promotes the v2.1.1 + v2.2.0 repeated
  audit finding from a lesson into a deterministic rule (`.agents/rules/git.md
  § Release Workflow`). E2E-verified across 6 cases.
- **PostToolUse tool-usage aggregator** (`.claude/hooks/track_tools.py`).
  Increments a per-session counter in `.memory/.session_tools.json`
  (ephemeral, gitignored) on every tool call. `stop_audit.py` consumes the
  session's bucket on each Stop hook and writes `tools_used: {tool: count}`
  into the `audit_history.jsonl` entry, then GCs buckets older than 7 days.
  Closes the v2.2 §Loose-ends item where `tools_used` was empty/wrong.
- **Lesson auto-promotion detector** in `_ecosystem_health.py`
  (`pending_promotions()`, `promotion_status()`). Scans `.memory/lessons.md`
  for items whose body contains recurrence vocabulary (REPEAT / recurred /
  2nd occurrence / promotion required / repeat→promote) and whose `Source:`
  line does not yet record `promoted to rule`. Surfaced in three places:
  `session_start.py` `## 📊 Ecosystem health` block (new `promotion:` row)
  plus a 🟡 PROMOTE LESSON → RULE action block when recommended; the
  `diag_dashboard.py` `## Lessons` section with the pending titles listed;
  the `--summary` mode (and `/diag_status`) gains a 5th `promotion:` row.
  Conservative heuristic — false negatives are fine, false positives create
  noise on every session start.

### Changed

- **`.agents/rules/git.md` § Release Workflow** — new section codifies the
  five release-commit invariants (plugin.json, CHANGELOG, task.md,
  activeContext, tag). Explicit guidance: don't plan the next sprint in the
  closing commit (that section's `[ ]` would trip the new guardrail).
- **`.memory/lessons.md`** — the «activeContext.md Sprint Goals desync»
  lesson is marked promoted with a pointer to the new rule + guardrail.

---

## [2.2.1] — 2026-05-23

Hotfix bundle from the post-v2.2.0 audit (🟡 75/100 — `.memory/audit_v2.2.0_release.md`).
v2.2.0 shipped the pre-push version-sync guardrail registered through pre-commit
framework. The standalone CLI worked correctly, but pre-commit framework on
Windows silently passed the hook (~0.07s) without actually executing the script
— Layer A's flagship deterministic guardrail was bypassable in real `git push`
flow. v2.2.1 fixes this and the long-running activeContext-vs-task.md desync gap.

### Fixed

- **Pre-push guardrail moved out of pre-commit framework into raw shim**
  (`.githooks/pre-push`). Activated via `git config core.hooksPath .githooks`
  (added to `bootstrap.ps1`, documented in `setup_environment.md`,
  `ENVIRONMENT_SETUP.md`, `deploy-fresh/SKILL.md`). The shim runs the
  version-sync check directly, then `exec`s `pre-commit hook-impl
  --hook-type pre-push` to delegate the remaining pre-push pipeline. Real
  `git push origin v9.9.9` (wrong version) is now hard-blocked with the full
  diagnostic; `check-version-sync` entry was removed from `.pre-commit-config.yaml`
  with an inline comment explaining why.
- **`scripts/check_version_sync.py::read_pushed_tags()`** rewritten to use
  `git tag --points-at HEAD` as the primary source (framework-independent),
  falling back to stdin parsing for direct-invocation tests. The previous
  stdin-only implementation was the second half of the v2.2.0 bug — even when
  invoked via raw hook, pre-commit's wrapper swallows git's stdin.
- **`scripts/train_reasoning_bank.py`** — `lesson_by_id = {l[…]: …}`
  renamed `l → lesson` (ruff E741 ambiguous-variable), pre-existing debt
  exposed by the E2E test running ruff over all files.

### Added

- **`scripts/test_pre_push_e2e.py`** — E2E test that invokes
  `.githooks/pre-push` directly with synthetic git pre-push stdin and
  asserts both blocking (wrong-version tag at HEAD → exit non-zero with
  VERSION SYNC FAILED) and pass-through (no wrong tag → version check
  doesn't fire). Closes the audit gap: v2.2.0 had unit tests but no
  integration test, which is precisely how the pre-commit-framework silent-
  skip bug slipped past.
- **`.memory/lessons.md` × 3 new entries:**
  «pre-commit framework silently skips pre-push hooks on Windows — use raw
  .githooks/ shim», «ship-prod-run-before-DONE applies to integration tests
  too», «activeContext.md Sprint Goals desync — repeat → promote to rule».
- **`.memory/audit_v2.2.0_release.md`** — full v2.2.0 post-release audit
  report (🟡 75/100, 15-item scorecard, devil's advocate, fix plan).

### Changed

- `plugin.json` 2.2.0 → 2.2.1.
- `.ecosystem.toml::ecosystem.version` synced to 2.2.1.
- `bootstrap.ps1` — appended `git config core.hooksPath .githooks` after
  `git init`, with green confirmation message.
- `activeContext.md` Sprint Goals — Phase 1-7 all `[x]`, v2.2.0 + v2.2.1
  marked as released (closes the REPEAT lesson item by example).

---

## [2.2.0] — 2026-05-23

Self-Diagnostic Ecosystem. Шесть фаз в `main`, три слоя гарантий: A —
детерминистические guardrail'ы (нельзя обойти), B — session-triggered
cron (триггер = открытие новой сессии, без OS-cron — портируется),
C — observability (дашборд и компактный health-блок в инжекте).

Ключевая архитектурная идея: **session-triggered cron**. Не OS-level
cron, не Anthropic-hosted scheduled-tasks. `session_start.py` считает
«долги» по журналам в `.memory/` и эмитит `🔴 X REQUIRED` / `🟡 X
RECOMMENDED` маркеры. Агент видит → запускает работу → пишет в журнал
→ долг сбрасывается до следующего цикла. Кросс-платформенно
(Win/macOS/Linux), self-contained в шаблоне.

### Added — Layer A (deterministic guardrails)

- **Pre-push version-sync guardrail** (`scripts/check_version_sync.py`).
  Блокирует `git push --tags`, если рассинхронизированы
  `.claude-plugin/plugin.json::version` ↔ последнее `## [X.Y.Z]` в
  CHANGELOG ↔ имя push'имого тега ↔ `.ecosystem.toml::ecosystem.version`
  (если есть). Standalone CLI + `--pre-push` режим (читает git stdin
  per `githooks(5)`). Зарегистрирован в `.pre-commit-config.yaml` со
  `stages: [pre-push]`. Включается через
  `pre-commit install --hook-type pre-push` (добавлено в setup-доки).
- **Hook health-check** (`scripts/check_hook_health.py`). Парсит
  `.claude/settings.json::hooks`, для каждого хука: проверяет
  существование файла, запускает с `HOOK_DRYRUN=1` + пустым JSON
  stdin, таймаут 10s. Пишет `{"event": "hook_health_check", "status":
  "ok"|"degraded", "failed_hooks": [...]}` в audit_history.jsonl.
  Поддерживает `--verbose`. Дополнен раздел «Hooks» в
  `scripts/health_check.py`.
- **Dry-run mode (`HOOK_DRYRUN=1`)** в каждом из 4 существующих
  хуков — early-return для безопасной проверки без side effects.

### Added — Layer B (session-triggered cron)

- **`.claude/hooks/_ecosystem_health.py`** — общий stdlib-only модуль
  с helper'ами: `audit_age_days`, `stop_hook_count_since_audit`,
  `last_audit_info`, `consolidate_age_days`, `hook_health_age_hours`,
  `lessons_count`. Combined verdict helpers: `audit_status` /
  `consolidate_status` / `hook_health_status`. Пороги
  (AUDIT_REQUIRED_DAYS=7, AUDIT_REQUIRED_STOP_HOOKS=20,
  CONSOLIDATE_RECOMMENDED_DAYS=30, HOOK_HEALTH_STALE_HOURS=24, …)
  живут здесь — единый источник правды для инжекта и дашборда.
- **Auto-audit trigger** в `session_start.py::emit_audit_freshness()`.
  Три состояния: 🔴 `AUDIT REQUIRED` (age≥7 OR stop_hook_count≥20) с
  window-hint `<last_audit_tag>..HEAD`; 🟡 `audit aging` (3-7 дней);
  silent (<3 дней).
- **Consolidate-memory trigger** в
  `session_start.py::emit_consolidate_freshness()` (симметрично).
  🟡 `CONSOLIDATE RECOMMENDED` если age ≥ 30 дней OR
  `lessons_count() >= 20`.
- **`/consolidate_lessons`** slash-команда — триггерит
  `anthropic-skills:consolidate-memory` и записывает
  `consolidate_complete` event в audit_history.jsonl.
- **New event types** в audit_history.jsonl: `hook_health_check`,
  `consolidate_complete`. Append-only, фильтрация по `event` field
  (lesson «append-only logs need event filters» применён).

### Added — Layer C (observability)

- **`scripts/diag_dashboard.py`** — markdown-отчёт по всем журналам:
  6 секций (Audits trend, Lessons + consolidate status, Retrieval mix,
  Trajectories outcomes, Hooks health, Version sync). `--summary` флаг
  → 4 строки светофоров. Использует общий `_ecosystem_health` модуль
  (одни и те же светофоры в инжекте и дашборде).
- **`/diag_status`** slash-команда — вызывает дашборд `--summary`,
  предлагает actions для каждого не-зелёного индикатора.
- **Unified `## 📊 Ecosystem health` блок** в инжекте session_start.py.
  4 строки (audit / lessons / hooks / version sync) — всегда выводится,
  заменяет старый `emit_lessons_freshness()`. Action-блоки
  (🔴 AUDIT REQUIRED / 🟡 CONSOLIDATE RECOMMENDED) остались ВЫШЕ
  summary для урgent видимости.

### Changed

- `plugin.json` 2.1.1 → 2.2.0.
- `.ecosystem.toml::ecosystem.version` обновлён через
  `update_ecosystem.py --apply` (self-sync).
- `.pre-commit-config.yaml` — добавлен `check-version-sync` блок со
  `stages: [pre-push]`.
- `scripts/health_check.py` — новый раздел «Hooks» (вызывает
  `check_hook_health.py`, прокидывает результат в overall pass/fail).
- Setup-доки (`setup_environment.md`, `ENVIRONMENT_SETUP.md`,
  `deploy-fresh/SKILL.md`) — инструкция запустить
  `pre-commit install --hook-type pre-push`.

### Fixed

- `session_start.py` — два f-string без плейсхолдеров (ruff F541),
  пред-существующий долг, exposed первым прогоном pre-push hook'а
  (запускает все pre-commit hook'и по умолчанию, включая ruff поверх
  всего репо).

---

## [2.1.1] — 2026-05-23

Hotfix bundle from the post-v2.1.0 audit (🟡 80/100 — three gaps recorded in
`.memory/audit_v2.1.0_release.md`). No new features; brings the released state
in line with what v2.1.0 advertised, plus three lessons.

### Fixed

- **`update_ecosystem.py::get_upstream_version()` was looking in the wrong place.**
  The function checked the repo root for `plugin.json`, but the real file lives at
  `.claude-plugin/plugin.json` (current Claude Code plugin layout). On a self-sync
  with `--apply`, the `version` field in `[ecosystem]` was silently skipped. Fixed
  by checking `.claude-plugin/plugin.json` first, then the root path as a legacy
  fallback.
- **`.ecosystem.toml` had no `[ecosystem]` section at all.** Spec L62 and prior
  `activeContext.md` both listed it as a release step that v2.1.0 skipped. A
  `python scripts/update_ecosystem.py --from . --apply` now writes the section
  with `version`, `upstream_sha`, and the full `[ecosystem.file_shas]` snapshot —
  the same data downstream consumers will see.
- **Phase 2 (trajectory ingest) had no production verification before tagging.**
  `.memory/session_trajectories.jsonl` was 0 bytes for the entire v2.1 sprint —
  the new write-path was never exercised on a real session. Backfilled by calling
  `record_session_trajectory()` directly on the v2.1.0 release commit; the file
  now has its first row.

### Added

- **`.memory/lessons.md` × 3 new lessons:** "Ship code paths with at least one
  prod run before declaring DONE", "Single-source-of-truth for project version
  (and verify on release)", "Release phase checkboxes belong in task.md, not
  activeContext.md". All cite the v2.1.0 post-release audit as source.
- **`task.md` § Phase 5 — Hotfix v2.1.1** with explicit checkboxes for each
  hotfix item, so the pre-commit guardrail (`check_task_guardrail.py`) actually
  gates release-phase state going forward.

### Changed

- `plugin.json` 2.1.0 → 2.1.1.
- `activeContext.md` — sprint focus moves to v2.1.1 release closure, v2.1 sprint
  marked done.

---

## [2.1.0] — 2026-05-23

Reasoning Bank distribution sprint. Three phases shipped to `main` over the
v2.1 spec (`docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md`):
hybrid retrieve, trajectory ingest, and a cross-platform downstream sync tool.
`plugin.json` version bumped from `1.0.0` → `2.1.0` (skipped on prior releases).

### Added

- **Phase 1 — Hybrid retrieve (BM25 + RRF)** in `scripts/reasoning_bank.py`.
  New `_bm25_retrieve()` and `_rrf_fuse()`; `retrieve()` dispatches on
  `mode ∈ {dense, sparse, hybrid}` with default `hybrid`. CLI `--mode` and
  `--rrf-k` flags. Sparse mode works without ChromaDB installed. `mode` field
  recorded in `.memory/retrieval_logs.jsonl`. Harness `scripts/test_reasoning_bank.py`
  (5/5 assertions). Merge `e9d73c5`.
- **Phase 2 — Trajectory ingest** (v2.1 schema). `session_start.py` writes
  `.memory/.session_start` (gitignored, idempotent over 12 h);
  `record_session_trajectory()` rewritten to v2.1 schema with `files_touched`,
  `duration_min`, `tools_used`. `ingest_reasoning_bank()` split into two
  bounded subprocesses (`ingest_lessons` + `ingest_trajectories`), each writing
  its own `audit_history.jsonl` row. Defensive parser tolerates legacy
  `files_changed`. Merge `52f3730`.
- **Phase 3 — Downstream distribution** via `scripts/update_ecosystem.py`.
  Cross-platform sync of `.claude/`, `.agents/`, `scripts/`, and `AGENTS.md`
  from an upstream template (local path or git URL — auto-clones into a
  tempdir, cleaned up in `finally`). Never touches `.memory/`, `.env*`,
  `task.md`, `.git/`, `.ecosystem.toml`. SHA snapshot in
  `[ecosystem.file_shas]` of `.ecosystem.toml` detects hand-edited files —
  blocked by default, overridable with `--force`. `--apply` refreshes the
  snapshot plus `[ecosystem].version` / `upstream_sha`. Default is dry-run
  with a per-status plan. Idempotent self-sync: `--from .` → 0 changes
  (45 unchanged). Commit `da14942`.

### Changed

- `TEMPLATE_README.md` §"Keeping the template up to date" rewritten around
  the new `update_ecosystem.py` workflow (replaces the manual-diff guidance).

---

## [2.0.1] — 2026-05-21

Hotfix bundle from the post-v2.0.0 sanity audit (🟢 92/100 via `ecosystem-auditor`
subagent). Two P1 follow-ups; no functional code changes.

### Fixed

- **CHANGELOG numeric drift** — Phase 3 bullet claimed "9 slash commands"; the
  actual count is **10** (8 existing commands + 2 new: `/model_check`,
  `/handoff`). Surfaced by the audit's Devil's-Advocate pass on the v2.0.0
  CHANGELOG.

### Added

- **First `audit_complete` row in `.memory/audit_history.jsonl`** — the v2.0.0
  audit-freshness fix (Phase 2 PR #2) had no production evidence yet because no
  `/audit_ecosystem` Phase E had run on the released state. This release
  records the v2.0.0 release-state audit (🟢 92/100, mode=`cross-session`,
  source=`ecosystem-auditor subagent`) so the freshness signal has its first
  real datapoint. Future audits append additional rows the same way.

---

## [2.0.0] — 2026-05-21

Production-readiness upgrade. Implemented over 6 stacked feature branches off the
v1.0 baseline (`7be1950`). See [`docs/specs/2026-05-21-production-readiness.md`](docs/specs/2026-05-21-production-readiness.md)
for the full spec and 17 architectural decisions.

### ⚠️ Breaking changes

- **`AGENTS.md` is now the source-of-truth for AI agent rules.** `CLAUDE.md` is
  auto-generated from `AGENTS.md` via `scripts/sync_agents_md.py` and a
  pre-commit hook (`agents-md-sync`) that refuses commits when the two are
  out of sync. **Action required:** edit `AGENTS.md` instead of `CLAUDE.md`.
  Rationale in [ADR-001](docs/adr/001-agents-md-source-of-truth.md).
- **`.claude/Skills/` renamed to `.claude/skills/`** (case-sensitive filesystem
  compatibility). Downstream consumers may need to update references.
- **Generic skills removed** (`deep-research`, `problem-solving`, `triz`).
  They are not part of the governance core and bloated the template. If you
  need them, install from upstream skill packs as a separate concern.
- **Default agent model is Opus 4.7.** Inverts the typical 2026 default —
  Sonnet 4.6 is used only on explicit safe-path triggers (small, mechanical,
  single-file edits). See [`.agents/rules/model-policy.md`](.agents/rules/model-policy.md).

### Added

**Phase 1 — Critical fixes**
- `AGENTS.md` as canonical rules source with `scripts/sync_agents_md.py`
  generator and `agents-md-sync` pre-commit hook.
- Bootstrap guard in `session_start.py` — emits `🔴 BOOTSTRAP REQUIRED` block
  when `${PROJECT_NAME}` placeholders are still present.

**Phase 2 — Distribution-readiness**
- `scripts/regenerate_plugin_manifest.py` + `plugin-manifest-sync` pre-commit
  hook (fixes drift between `plugin.json` and actual `.claude/` surface).
- `.claude-plugin/marketplace.json` scaffold for plugin distribution.

**Phase 3 — Model routing**
- `.agents/rules/model-policy.md` (~155 lines) — Always-Opus allowlist,
  Sonnet safe-path whitelist, Context Window Awareness, Model Switch
  Checkpoint, silent subagent delegation, block-format spec.
- `model:` frontmatter on all 10 slash commands (8 existing + 2 new); `ecosystem-auditor` pinned
  to `model: opus`.
- New slash commands `/model_check` and `/handoff`.

**Phase 4 — Planning detector + context monitor**
- `.claude/hooks/planning_hint.py` (UserPromptSubmit) — emits unified
  `🧭 PLAN + 💡 MODEL` block on RU/EN architectural triggers and ≥3-file-refs
  heuristic; honours `CLAUDE_DISABLE_PLANNING_HINT=1` killswitch.
- Context-window monitor in `session_start.py` (transcript-size heuristic →
  `🔄 SESSION HANDOFF` at 70%, `❌` critical at 90%).

**Phase 5 — ReasoningBank auto-ingest**
- `scripts/finalize_session.py` gains `ingest_reasoning_bank()` — bounded
  subprocess call (`timeout=30`, status mapped to `ok` / `skipped` / `timeout`
  / `error`), structured row written to `.memory/audit_history.jsonl`,
  non-blocking on missing `chromadb`.

**Phase 6a — Mechanical cleanup**
- `outputStyle: default` declared explicitly in `.claude/settings.json`.
- `bootstrap.ps1` pyproject scaffold: `[project.optional-dependencies] dev`
  with ruff/pytest/pre-commit, `[tool.ruff.format]`, pytest `addopts`.
- `.env.example` enriched with `ANTHROPIC_API_KEY`, `HTTPS_PROXY`,
  `CLAUDE_DISABLE_PLANNING_HINT`.

**Phase 6b — Design bundle**
- Subagent `.claude/agents/code-reviewer.md` (`model: opus`) — independent
  diff review with severity rubric (P0–P3), 4-axis analysis, devil's-advocate
  phase, read-only contract.
- Subagent `.claude/agents/researcher.md` (`model: sonnet`) — open-ended
  investigation, cite-everything, time-boxed web research.
- `.claude/hooks/statusline.py` — renders `🤖 <model> | 🌿 <branch> | 📊 <ctx%>`;
  registered under top-level `statusLine` in `settings.json`.
- ADR-001 ([`docs/adr/001-agents-md-source-of-truth.md`](docs/adr/001-agents-md-source-of-truth.md))
  as a worked example.
- [`docs/template-design.md`](docs/template-design.md) — rationale doc that
  survives `bootstrap.ps1` so downstream projects retain the architecture story.

### Changed

- `TEMPLATE_README.md` slimmed: feature list refreshed with current counts and
  AGENTS.md emphasis, cross-reference to `docs/template-design.md` for
  rationale, directory layout shows all 5 hooks + 3 subagents.
- `.claude/agents/ecosystem-auditor.md` bumped to `model: opus`.
- `.memory/claude_code_state.md` → `.memory/api_reference_hooks.md` (more
  honest name — it's an API snapshot, not project state) + heading refresh.
- `bootstrap.ps1` pyproject scaffold drops deprecated `ANN101`/`ANN102` ignores
  (removed in ruff 0.5).
- `CLAUDE.md` regenerated from `AGENTS.md` (now carries an auto-generated
  header).

### Fixed

- **Audit-freshness signal was silently broken**: `audit_history.jsonl` is
  appended to by `stop_audit.py` on every turn, so `lines[-1]` / file-mtime
  checks always reported the log as fresh and the "no full audit in N days"
  signal could never fire. Filtered by `event == "audit_complete"` across
  `session_start.py`, `stop_audit.py`, `finalize_session.py`; producers
  (`/audit_ecosystem` Phase E) now explicitly emit the marker. Lesson
  captured in `.memory/lessons.md` ("Don't measure freshness by mtime or
  last-line on a write-heavy log").
- `model-policy.md` cross-reference table no longer contains `(Phase 4)`
  placeholder labels.

### Removed

- `.claude/Skills/deep-research/`, `.claude/Skills/problem-solving/`,
  `.claude/Skills/triz/` — generic skills, not part of the governance core
  (~6,500 lines).
- `scripts/monitor_context.sh` — superseded by the context monitor inside
  `session_start.py` (PR #4).
- Stale `monitor_context.py` reference and old `claude_code_state.md` entry
  from `TEMPLATE_README.md`'s directory layout.

### Maturity

This release lifts the template from the 82/100 score recorded in the
2026-05-21 baseline audit. A re-audit on the released state is recommended
(`/audit_ecosystem`) — target ≥90/100.

---

## [1.0] — initial template baseline

See commit `40d576c feat: initialize claude-ecosystem-template v1.0`.
