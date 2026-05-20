# Active Context

> **Updated:** 2026-05-21 — handoff prep
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.0.0 Production-Readiness Upgrade — Phase 0 complete, Phase 1 ready to start in new session.**

Audit (82/100) → 17 architectural decisions confirmed → Spec + Plan written → Ready for implementation.

## Sprint Goals

Ship v2.0.0 across 6 PRs. Each PR = one phase, one branch `feat/v2.0.0-phase-{N}-<topic>`.

- [x] Phase 0 — Audit + Spec + Plan + task.md prep
- [ ] Phase 1 — Critical fixes (skills rename, AGENTS.md, bootstrap guard) — **NEXT**
- [ ] Phase 2 — Distribution-readiness (plugin.json auto-regen, marketplace.json, audit freshness)
- [ ] Phase 3 — Model Routing System + Context Window Awareness + /handoff
- [ ] Phase 4 — Planning Phase Detector + Context Monitor
- [ ] Phase 5 — ReasoningBank auto-ingest
- [ ] Phase 6 — Cleanup + new subagents + statusline + pyproject scaffold

## Recent Changes

- **2026-05-21:** Deep ecosystem audit performed → maturity 82/100.
- **2026-05-21:** Plan approved via ExitPlanMode. Spec written: [docs/specs/2026-05-21-production-readiness.md](../docs/specs/2026-05-21-production-readiness.md). Working plan: `~/.claude/plans/parallel-leaping-rainbow.md`.
- **2026-05-21:** Three new decisions added — #1a Context Window Awareness, #1b Model Switch Checkpoint (blocking), #1c Hybrid execution via subagents with explicit model.

## Key Decisions (17, all in spec)

Highlights:
- **Default model:** Opus 4.7. Sonnet 4.6 only on explicit safe-path triggers (inversion of typical 2026 pattern — respects quality priority).
- **AGENTS.md** = source-of-truth; CLAUDE.md = auto-generated via `scripts/sync_agents_md.py` + pre-commit guard.
- **Planning + Model + Session handoff hints** — three deterministic blocks (`🧭 PLAN`, `💡 MODEL`, `🔄 SESSION`) wired through UserPromptSubmit hook + AGENTS.md rule.
- **Version bump:** v1.0 → v2.0.0 (breaking changes: skills rename, removed generic skills, AGENTS.md replaces CLAUDE.md as source).

## Blockers / Open Questions

None — all 17 forks resolved.

## Next Steps (for next session)

**START HERE:** open new Claude Code session, then:

1. Stay on **Opus 4.7** (default start — user preference #1d, reliability first).
2. Say: **"новая сессия, продолжаем работу"**
3. I'll read this file + spec + task.md, then start PR #1.
4. I'll silently delegate mechanical chunks to Sonnet via subagents (`Agent(model="sonnet", ...)`) — no need to switch your main model.
5. I'll only block-stop with `💡 MODEL` block if both (a) Sonnet is unsafe for the current chunk AND (b) subagent delegation is impossible. Otherwise — no model-switch noise.
6. Work through 18 steps in `task.md`. Mark `[x]` each step.
7. Verify with PR #1 verification block in spec.
8. Open PR via `gh pr create`.

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
