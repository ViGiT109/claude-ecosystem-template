# Active Context

> **Updated:** 2026-05-21 — Phase 2 complete on `feat/v2.0.0-phase-2-distribution-readiness`
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.0.0 Production-Readiness Upgrade — Phase 2 implementation complete. Phase 3 next.**

Audit (82/100) → 17 architectural decisions confirmed → Spec + Plan written → PR #1 (Phase 1) + PR #2 (Phase 2) implemented and verified.

## Sprint Goals

Ship v2.0.0 across 6 PRs. Each PR = one phase, one branch `feat/v2.0.0-phase-{N}-<topic>`.

- [x] Phase 0 — Audit + Spec + Plan + task.md prep
- [x] Phase 1 — Critical fixes (skills rename, AGENTS.md, bootstrap guard) — **PR open**
- [x] Phase 2 — Distribution-readiness (plugin.json auto-regen, marketplace.json, audit freshness fix) — **branch ready**
- [ ] Phase 3 — Model Routing System + Context Window Awareness + /handoff — **NEXT**
- [ ] Phase 4 — Planning Phase Detector + Context Monitor
- [ ] Phase 5 — ReasoningBank auto-ingest
- [ ] Phase 6 — Cleanup + new subagents + statusline + pyproject scaffold

## Recent Changes

- **2026-05-21:** Deep ecosystem audit performed → maturity 82/100.
- **2026-05-21:** Plan approved via ExitPlanMode. Spec written: [docs/specs/2026-05-21-production-readiness.md](../docs/specs/2026-05-21-production-readiness.md). Working plan: `~/.claude/plans/parallel-leaping-rainbow.md`.
- **2026-05-21:** Three new decisions added — #1a Context Window Awareness, #1b Model Switch Checkpoint (blocking), #1c Hybrid execution via subagents with explicit model.
- **2026-05-21:** PR #1 implemented on `feat/v2.0.0-phase-1-critical-fixes` — 4 commits: Skills→skills rename, generic-skill removal, bootstrap guard in session_start.py, AGENTS.md source-of-truth + sync_agents_md.py + agents-md-sync pre-commit hook.
- **2026-05-21:** PR #2 implemented on `feat/v2.0.0-phase-2-distribution-readiness`: `scripts/regenerate_plugin_manifest.py` + `plugin-manifest-sync` pre-commit hook (fixed drift — `initialize_project.md` was missing); `.claude-plugin/marketplace.json` scaffold; **fixed latent bug** — audit-freshness signal in `session_start.py` / `stop_audit.py` / `finalize_session.py` now filters `audit_history.jsonl` by `event == "audit_complete"` (previously masked by every-turn `stop_hook` entries); `/audit_ecosystem` Phase E now emits the marker.

## Key Decisions (17, all in spec)

Highlights:
- **Default model:** Opus 4.7. Sonnet 4.6 only on explicit safe-path triggers (inversion of typical 2026 pattern — respects quality priority).
- **AGENTS.md** = source-of-truth; CLAUDE.md = auto-generated via `scripts/sync_agents_md.py` + pre-commit guard.
- **Planning + Model + Session handoff hints** — three deterministic blocks (`🧭 PLAN`, `💡 MODEL`, `🔄 SESSION`) wired through UserPromptSubmit hook + AGENTS.md rule.
- **Version bump:** v1.0 → v2.0.0 (breaking changes: skills rename, removed generic skills, AGENTS.md replaces CLAUDE.md as source).

## Blockers / Open Questions

None — all 17 forks resolved.

## Next Steps (for next session)

PR #1 and PR #2 are both branched (stacked). Before starting Phase 3:

1. Push `feat/v2.0.0-phase-2-distribution-readiness` and open PR #2 (stacked on PR #1) when remote is configured.
2. Then say: **«новая сессия, начинаем Phase 3»**
3. Phase 3 scope (PR #3): `.agents/rules/model-policy.md` (Opus design) + frontmatter `model:` in 8 commands + `ecosystem-auditor.md` model bump + `/model_check` + `/handoff` slash-commands.
4. Continue silent subagent delegation pattern (Sonnet for mechanical implementation, Opus stays as main).

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
