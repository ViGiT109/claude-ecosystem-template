# Task: v2.1 — Hybrid Retrieval + Trajectory Ingest + Downstream Distribution

**Spec:** [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md)
**Status:** Spec approved 2026-05-22 — 4 open questions resolved. Ready to start Phase 1.
**Estimated:** 8–12 h, ~10 files, 4 phases, 4 PRs.

## Phase 1 — Hybrid retrieve (`feat/v2.1-phase-1-hybrid-retrieve`)

- [ ] Add `rank-bm25` to `pyproject.toml::[project.optional-dependencies] reasoning`
- [ ] Implement `_bm25_retrieve(query, top_k)` in `reasoning_bank.py` — parses lessons.md, builds BM25Okapi, returns ranked list. `lru_cache` keyed on `lessons.md` mtime
- [ ] Implement `_rrf_fuse(dense_results, sparse_results, k=60)` — Reciprocal Rank Fusion merge
- [ ] Refactor `retrieve()` to dispatch on `mode ∈ {dense, sparse, hybrid}` (default: `hybrid`)
- [ ] CLI: add `--mode` and `--rrf-k` flags; sparse mode must work without chromadb installed (separate code path, no chromadb import)
- [ ] Log `mode` field in `retrieval_logs.jsonl`
- [ ] Write a query-harness test (`scripts/test_reasoning_bank.py` or `if __name__` block) — fixed set: exact-token query ("audit_history") + paraphrase ("when did we last audit") + multilingual ("аудит экосистемы")
- [ ] Commit, push, verify pre-commit clean

## Phase 2 — Trajectory ingest (`feat/v2.1-phase-2-trajectory-ingest`)

- [ ] Extend `finalize_session.py::record_session_trajectory()` to write JSONL row with expanded schema: `{date, commit_msg, outcome, task_completion, files_touched, duration_min, tools_used}`
- [ ] Update `reasoning_bank.py::parse_trajectories()` to read new fields; keep `document` string as 3-field summary for embedding stability
- [ ] Extend `finalize_session.py::ingest_reasoning_bank()` — second bounded subprocess for `ingest_trajectories`; two separate `audit_history.jsonl` rows (`event: "reasoning_bank_ingest_lessons"`, `..._trajectories`)
- [ ] Smoke test: run `finalize_session.py` locally, verify trajectory row + two audit rows
- [ ] Commit, push, verify pre-commit clean

## Phase 3 — Downstream distribution (`feat/v2.1-phase-3-update-ecosystem`)

- [ ] Create `scripts/update_ecosystem.py` — clones upstream into temp dir, computes per-file diff for `.claude/`, `.agents/`, `scripts/`, root hooks/configs
- [ ] Default `--dry-run`; require `--apply` for writes
- [ ] SHA-protect `CLAUDE.md` / `AGENTS.md` against last `.ecosystem.toml` snapshot; require `--force` if user-edited
- [ ] Skiplist: `.memory/`, `.env*`, `task.md`, `*.local.*`
- [ ] On `--apply`: update `.ecosystem.toml::version` and `.ecosystem.toml::upstream_sha`
- [ ] Idempotency test: `update_ecosystem.py --from . --dry-run` against self → empty diff
- [ ] Update `TEMPLATE_README.md` §"Keeping the template up to date" — replace manual-diff prose with `update_ecosystem.py` usage
- [ ] Commit, push, verify pre-commit clean

## Phase 4 — Release (`release/v2.1.0`)

- [ ] Bump version in `plugin.json` + `.ecosystem.toml` → `2.1.0`
- [ ] `CHANGELOG.md` v2.1.0 entry (Added: hybrid retrieve, trajectory ingest, update_ecosystem; Changed: retrieve default mode)
- [ ] Update `.memory/activeContext.md` with v2.1 sprint completion
- [ ] Tag `v2.1.0` (annotated), push to origin, GitHub release
- [ ] Run `ecosystem-auditor` subagent on released state — target ≥85/100

## Acceptance (mirror of spec)

- [ ] `retrieve --mode hybrid` returns both exact-token + paraphrase matches on test query set
- [ ] `retrieve --mode sparse` works without chromadb installed
- [ ] `finalize_session.py` produces one trajectory row + two audit_history rows per finalize
- [ ] `update_ecosystem.py --dry-run` against self → zero diff (idempotent)
- [ ] `update_ecosystem.py --apply` updates `.claude/` in a downstream test dir without touching `.memory/`
- [ ] `rank-bm25` listed in `[project.optional-dependencies] reasoning`; missing dep → friendly error
- [ ] CHANGELOG v2.1 written; `plugin.json` + `.ecosystem.toml` bumped
- [ ] Post-release audit ≥85/100
