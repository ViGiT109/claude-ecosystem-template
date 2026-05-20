# Task: v2.0.0 Phase 0 — Audit + Plan + Spec (COMPLETE)

**Status:** Phase 0 closed. Phase 1 (PR #1) to be opened in **new session** for clean context window.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Phase 0 Steps (this session)

- [x] Deep ecosystem audit (82/100 maturity score)
- [x] Web research — 2026 best practices benchmark
- [x] 17 architectural decisions agreed via AskUserQuestion (3 rounds)
- [x] Plan written to `~/.claude/plans/parallel-leaping-rainbow.md`
- [x] Spec written to `docs/specs/2026-05-21-production-readiness.md`
- [x] Context Window Awareness factor added to plan/spec (decision #1a)
- [x] activeContext.md updated for session handoff
- [x] task.md reset for clean Phase 0 commit

## Next session — what to do

> **Open new Claude Code session, then:**
>
> 1. `/new_session` (auto-loads activeContext, lessons, git status)
> 2. Tell me: **«продолжаем работу над v2.0.0 — начинаем PR #1»**
> 3. `/model claude-sonnet-4-6` (Phase 1 is mechanical)
> 4. I'll replace this file with PR #1 step-list and start work.

## Why new session?

This session's context is at ~185K. Sonnet 4.6 has a 200K window — switching now would hit the wall immediately. Fresh session = 200K available = clean run through PR #1.
