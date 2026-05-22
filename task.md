# Task: v2.1 Reasoning Bank Distribution

**Spec:** [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md)
**Sprint progress:** tracked in [.memory/activeContext.md](.memory/activeContext.md)

## Phase 1 — Hybrid retrieve — **DONE** (merged)

- [x] `pyproject.toml` created; `rank-bm25` added to `[project.optional-dependencies] reasoning`
- [x] `_bm25_retrieve()` + `_rrf_fuse()` implemented in `scripts/reasoning_bank.py`
- [x] `retrieve()` dispatches on `mode ∈ {dense, sparse, hybrid}`, default hybrid
- [x] CLI `--mode` / `--rrf-k` flags; graceful degradation when chromadb missing
- [x] `mode` field logged in `.memory/retrieval_logs.jsonl`
- [x] Query-harness `scripts/test_reasoning_bank.py` — 5 assertions, all pass

## Phase 2 — Trajectory ingest — **DONE** (merged)

- [x] `session_start.py::record_session_start()` writes `.memory/.session_start` (gitignored, idempotent 12 h)
- [x] `record_session_trajectory()` rewritten to v2.1 schema (`files_touched`, `duration_min`, `tools_used: []`)
- [x] `ingest_reasoning_bank()` split into two bounded subprocesses (`ingest_lessons` + `ingest_trajectories`)
- [x] Each writes its own `audit_history.jsonl` row
- [x] `parse_trajectories()` defensive `.get()` + legacy `files_changed` fallback

## Phase 3 — Downstream distribution — **NEXT**

Branch: `feat/v2.1-phase-3-update-ecosystem`. Scope and acceptance criteria defined in spec.

## Phase 4 — Release v2.1.0

CHANGELOG, version bump in `plugin.json` + `.ecosystem.toml`, annotated tag, post-release audit ≥85/100.
