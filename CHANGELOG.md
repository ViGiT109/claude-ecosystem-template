# Changelog

All notable changes to this project are documented here.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

<!-- Add changes here as they are made -->

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
