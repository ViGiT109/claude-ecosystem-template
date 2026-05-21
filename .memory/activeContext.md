# Active Context

> **Updated:** 2026-05-21 — **v2.0.0 released.** Tag `v2.0.0` on `main` at the release commit.
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.0.0 Production-Readiness Upgrade — SHIPPED.** Six phases (1, 2, 3, 4, 5, 6a, 6b) merged into `main` via fast-forward; CHANGELOG written; tag `v2.0.0` cut.

Audit (82/100) → 17 architectural decisions confirmed → Spec + Plan written → PRs #1–#5 + #6a + #6b implemented, verified, and released. Phase 6 was split into 6a (mechanical) + 6b (design) per user direction during execution.

## Sprint Goals

Ship v2.0.0 across 6 PRs. Each PR = one phase, one branch `feat/v2.0.0-phase-{N}-<topic>`.

- [x] Phase 0 — Audit + Spec + Plan + task.md prep
- [x] Phase 1 — Critical fixes (skills rename, AGENTS.md, bootstrap guard) — **PR open**
- [x] Phase 2 — Distribution-readiness (plugin.json auto-regen, marketplace.json, audit freshness fix) — **branch ready**
- [x] Phase 3 — Model Routing System (model-policy.md, frontmatter in 8 commands, ecosystem-auditor→opus, /model_check, /handoff) — **branch ready**
- [x] Phase 4 — Planning Phase Detector + Context Monitor (planning_hint.py UserPromptSubmit hook, context-window monitor in session_start.py, AGENTS.md signaling sections) — **branch ready**
- [x] Phase 5 — ReasoningBank auto-ingest (finalize_session.py → bounded subprocess to reasoning_bank.py ingest_lessons; status row in audit_history.jsonl) — **branch ready**
- [x] Phase 6a — Mechanical cleanup (rm monitor_context.sh, rename claude_code_state.md → api_reference_hooks.md, outputStyle, pyproject scaffold tooling, .env.example enrichment) — **branch ready**
- [x] Phase 6b — Design bundle (code-reviewer + researcher subagents, statusline.py hook, ADR-001, docs/template-design.md, TEMPLATE_README.md slim) — **branch ready**
- [x] Release — CHANGELOG v2.0.0 written, fast-forward merge to main, tag `v2.0.0` cut — **DONE**

## Recent Changes

- **2026-05-21:** Deep ecosystem audit performed → maturity 82/100.
- **2026-05-21:** Plan approved via ExitPlanMode. Spec written: [docs/specs/2026-05-21-production-readiness.md](../docs/specs/2026-05-21-production-readiness.md). Working plan: `~/.claude/plans/parallel-leaping-rainbow.md`.
- **2026-05-21:** Three new decisions added — #1a Context Window Awareness, #1b Model Switch Checkpoint (blocking), #1c Hybrid execution via subagents with explicit model.
- **2026-05-21:** PR #1 implemented on `feat/v2.0.0-phase-1-critical-fixes` — 4 commits: Skills→skills rename, generic-skill removal, bootstrap guard in session_start.py, AGENTS.md source-of-truth + sync_agents_md.py + agents-md-sync pre-commit hook.
- **2026-05-21:** PR #2 implemented on `feat/v2.0.0-phase-2-distribution-readiness`: `scripts/regenerate_plugin_manifest.py` + `plugin-manifest-sync` pre-commit hook (fixed drift — `initialize_project.md` was missing); `.claude-plugin/marketplace.json` scaffold; **fixed latent bug** — audit-freshness signal in `session_start.py` / `stop_audit.py` / `finalize_session.py` now filters `audit_history.jsonl` by `event == "audit_complete"` (previously masked by every-turn `stop_hook` entries); `/audit_ecosystem` Phase E now emits the marker.
- **2026-05-21:** PR #3 implemented on `feat/v2.0.0-phase-3-model-routing`: new `.agents/rules/model-policy.md` (~155 lines, Opus design — philosophy, Always-Opus allowlist, Sonnet safe-path whitelist, Context Window Awareness, Model Switch Checkpoint, silent subagent delegation, block-format spec, cross-reference table); `model:` frontmatter added to all 8 slash-commands (audit/initialize/create_spec/extract_lesson → opus; commit_release/setup_environment → sonnet; new_session/agentic_tdd → inherit); `ecosystem-auditor.md` bumped to `model: opus`; new `/model_check` and `/handoff` commands; AGENTS.md modular-rules table extended with Model Policy row; plugin.json regenerated (now 11 commands). Execution pattern: Opus main thread for 3.1 design, Sonnet subagent silent delegation for 3.2–3.5.
- **2026-05-21:** PR #5 implemented on `feat/v2.0.0-phase-5-reasoning-bank-ingest`: `scripts/finalize_session.py` gains `ingest_reasoning_bank()` — bounded (`timeout=30`, `check=False`, `capture_output=True`) subprocess call to `python scripts/reasoning_bank.py ingest_lessons`; status mapped to `ok` / `skipped` (non-zero exit, e.g. missing chromadb) / `timeout` (TimeoutExpired) / `error` (any other Exception); appends one row to `.memory/audit_history.jsonl` with `event: "reasoning_bank_ingest"`, `timestamp`, `status`, `returncode`, `stdout_tail`, `stderr_tail`, `duration_s`; one-line human summary printed; wired into `main()` between `collect_session_metrics()` and `record_session_trajectory()`. Smoke test on current env (no chromadb) produced `status: "skipped"`, returncode 1, full stderr captured, no SystemExit. Pre-commit guards (`agents-md-sync`, `plugin-manifest-sync`) stay green — pure script edit, no manifests touched.
- **2026-05-21:** **v2.0.0 released.** `feat/v2.0.0-phase-6b-design-bundle` fast-forward-merged into `main` (12 commits, stack tip `ea82587`). `CHANGELOG.md` rewritten with full v2.0.0 entry — breaking changes section calls out AGENTS.md source-of-truth shift, `Skills/`→`skills/` rename, removal of 3 generic skills, Opus-default model policy. Tag `v2.0.0` cut on the release commit. Stacked feature branches kept locally for audit trail (not deleted). Remote (origin `ViGiT109/claude-ecosystem-template`) only has Phase 1 branch pushed; push of `main` + tag pending user direction.
- **2026-05-21:** PR #6b implemented on `feat/v2.0.0-phase-6b-design-bundle` (design half of original Phase 6): new subagents `code-reviewer.md` (Opus — independent diff review with severity rubric, devil's-advocate phase, 4-axis analysis) + `researcher.md` (Sonnet — open-ended investigation, cite-everything, time-boxed web research, no-clarification rule); new `.claude/hooks/statusline.py` reads stdin JSON, outputs `🤖 <model> | 🌿 <branch> | 📊 <ctx%>` with graceful fallback when git/transcript absent, registered under top-level `statusLine` in `.claude/settings.json`; ADR-001 `docs/adr/001-agents-md-source-of-truth.md` as worked example documenting the AGENTS.md decision; both `docs/adr/README.md` and `docs/specs/README.md` indexes updated with real rows; new `docs/template-design.md` (~140 lines, captures Progressive Disclosure, Self-Improvement Loop, three-level memory, hooks-in-Python rationale, Opus-default policy, "what's intentionally absent") and survives bootstrap; `TEMPLATE_README.md` slimmed (refreshed feature list with current counts, cross-reference to design doc, removed "Maturity history" section absorbed by design doc, updated directory layout to include all 5 hooks + 3 subagents); `plugin.json` regenerated to register new agents + hook. Smoke tests: statusline.py outputs correct line on `{}` / empty stdin / bogus JSON / rich payload paths; both pre-commit guards green.
- **2026-05-21:** PR #6a implemented on `feat/v2.0.0-phase-6a-mechanical-cleanup` (split from Phase 6 per user direction; design half deferred to PR #6b): removed `scripts/monitor_context.sh` (obsolete since PR #4's `session_start.py` context monitor); renamed `.memory/claude_code_state.md` → `.memory/api_reference_hooks.md` + updated heading; cleaned cross-refs in `TEMPLATE_README.md`; added explicit `"outputStyle": "default"` to `.claude/settings.json`; enriched `bootstrap.ps1` pyproject scaffold with `[project.optional-dependencies] dev = [ruff>=0.6, pytest>=8.0, pre-commit>=3.5]`, `[tool.ruff.format]`, and `addopts` for pytest; dropped deprecated `ANN101`/`ANN102` ignore (removed in ruff 0.5); `.env.example` gained `ANTHROPIC_API_KEY`, `HTTPS_PROXY`, `CLAUDE_DISABLE_PLANNING_HINT` with explanatory comments. Pre-commit guards (`agents-md-sync`, `plugin-manifest-sync`) both green — no hook/skill/command surface touched.
- **2026-05-21:** PR #4 implemented on `feat/v2.0.0-phase-4-planning-hint`: new `.claude/hooks/planning_hint.py` (UserPromptSubmit, RU+EN regex triggers, ≥3-file-refs heuristic, `CLAUDE_DISABLE_PLANNING_HINT=1` killswitch, <20-char whitelist, emits unified 🧭 PLAN + 💡 MODEL block); context-window monitor added to `session_start.py` (transcript-size heuristic against `MODEL_WINDOWS` table, respects `CLAUDE_MODEL` env, 70%→🔄 SESSION HANDOFF, 90%→❌ critical); `.claude/settings.json` gains `UserPromptSubmit` registration (timeout 3s); AGENTS.md gains «Planning-phase signaling» and «Session handoff signaling» sections + extended deterministic-hooks table; `model-policy.md` cross-reference table trimmed of "(Phase 4)" placeholders; CLAUDE.md re-synced; plugin.json regenerated to include the new hook. Smoke tests pass: RU/EN triggers fire, heuristic fires on 4+ file refs, short prompts + killswitch + empty stdin all silent, context monitor stays silent under 70% and emits both SHRD/critical variants above thresholds.

## Key Decisions (17, all in spec)

Highlights:
- **Default model:** Opus 4.7. Sonnet 4.6 only on explicit safe-path triggers (inversion of typical 2026 pattern — respects quality priority).
- **AGENTS.md** = source-of-truth; CLAUDE.md = auto-generated via `scripts/sync_agents_md.py` + pre-commit guard.
- **Planning + Model + Session handoff hints** — three deterministic blocks (`🧭 PLAN`, `💡 MODEL`, `🔄 SESSION`) wired through UserPromptSubmit hook + AGENTS.md rule.
- **Version bump:** v1.0 → v2.0.0 (breaking changes: skills rename, removed generic skills, AGENTS.md replaces CLAUDE.md as source).

## Blockers / Open Questions

None — all 17 forks resolved.

## Next Steps (post-v2.0.0)

v2.0.0 has shipped locally. Open follow-ups:

1. **Push** `main` + tag `v2.0.0` to `origin` (and optionally the stacked feature branches for review history) — pending user direction. Suggested: `git push origin main --follow-tags`.
2. **GitHub release** — draft notes from the CHANGELOG section. Can use `gh release create v2.0.0 --notes-file …` once main is pushed.
3. **Sanity audit** — run `/audit_ecosystem` (or invoke the `ecosystem-auditor` subagent) on the released state. Target ≥90/100. Anything <85 → open a v2.0.1 follow-up.
4. **Cleanup (optional)** — delete the stacked `feat/v2.0.0-phase-*` branches locally once you no longer need them for archeology (`git branch -d …`). They are reachable via tags-and-merges history anyway.

Beyond v2.0.0: roadmap candidates include hybrid BM25+vector search in `reasoning_bank.py` (v2.1), trajectory ingest alongside lessons, and an `npx update-ecosystem` flow for downstream consumers (mentioned in TEMPLATE_README.md).

## Resume context

- **Spec:** [docs/specs/2026-05-21-production-readiness.md](../docs/specs/2026-05-21-production-readiness.md) — start here.
- **Working plan (local):** `C:\Users\vibev\.claude\plans\parallel-leaping-rainbow.md` — granular details.
- **Audit artefacts:** in conversation transcript (not persisted) — but conclusions are all in spec.
- **Task.md:** Phase 0 complete; replace with Phase 1 steps when starting PR #1.

## Model policy for this work (4 final decisions)

- **#1d Default start:** Opus 4.7 in every new session (user preference, reliability).
- **#1c Subagents:** silent delegation to Sonnet/Opus via `Agent(model=...)` — no announcement, no blocking.
- **#1b Checkpoint blocking:** only when user-side `/model` switch is the only path. Else silent.
- **#1a Context awareness:** if session ctx >70% — show `🔄 NEW SESSION RECOMMENDED`.
