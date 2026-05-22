# Task: v2.1 Phase 2 — Trajectory Ingest

**Spec:** [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md) §"Phase 2"
**Branch:** `feat/v2.1-phase-2-trajectory-ingest` (off `main` — phases independent per spec L152)
**Phase 1 status:** done locally on `feat/v2.1-phase-1-hybrid-retrieve` (commit `a70de39`) — separate PR.
**Phase 3/4:** out of scope for this branch — tracked in spec, will get their own `task.md` later.

## Goal

Make `finalize_session.py` write the full v2.1 trajectory schema and trigger
**both** `ingest_lessons` and `ingest_trajectories` as separate bounded subprocesses,
each producing its own `audit_history.jsonl` row.

## Schema target (spec L131)

```json
{"date": "...", "commit_msg": "...", "outcome": "...",
 "task_completion": "...", "files_touched": ["..."],
 "duration_min": 12.4, "tools_used": []}
```

Today's row has `files_changed` (→ rename to `files_touched`) and lacks
`duration_min` + `tools_used`.

## Steps

- [x] Add session-start timestamping to `.claude/hooks/session_start.py` — writes
      `.memory/.session_start` (single-line JSON: `{"started_at": "<ISO>"}`).
      Idempotent: only writes if file is missing OR older than 12 h.
- [x] Add `.memory/.session_start` to `.gitignore` (ephemeral, not project state).
- [x] Update `scripts/finalize_session.py::record_session_trajectory()`:
  - rename `files_changed` → `files_touched`
  - add `duration_min` — diff `now` against `.memory/.session_start::started_at`, round to 1 dp
  - add `tools_used: []` (placeholder — no aggregator yet; not in acceptance criteria)
  - keep existing fields (date, commit_msg, task_completion, outcome) — backward-compatible
- [x] Split `scripts/finalize_session.py::ingest_reasoning_bank()` into TWO bounded
      subprocess calls (`ingest_lessons` + `ingest_trajectories`), each with its own
      `audit_history.jsonl` row (`event: "reasoning_bank_ingest_lessons"` /
      `"reasoning_bank_ingest_trajectories"`). Shared helper for both.
- [x] Update `scripts/reasoning_bank.py::parse_trajectories()` — read new fields
      defensively via `.get()`; embedding document stays 3-field (spec L131).
- [x] Smoke-test: append a fake trajectory row → run `ingest_trajectories` →
      verify no crash + audit_history row written.
- [x] Update `.memory/activeContext.md` — Phase 2 done.
- [x] Commit (no push yet — user decides when to open PR).

## Acceptance (spec L110)

- [x] `finalize_session.py` writes one row to `session_trajectories.jsonl` per finalize.
- [x] Both `ingest_lessons` + `ingest_trajectories` triggered; both statuses in `audit_history.jsonl`.
- [x] New schema honored; old rows still parse (defensive `.get()`).

## Out of scope (not in this PR)

- `tools_used` real aggregator (deferred — placeholder empty list).
- ChromaDB schema migration (existing collections stay).
- v2.1.0 release / CHANGELOG (Phase 4).
- `update_ecosystem.py` (Phase 3).
