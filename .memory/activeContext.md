# Active Context

> **Updated:** 2026-05-22 — v2.1 spec approved; implementation pending in next session.
> Loaded automatically by `session_start.py` hook (first 25 lines).

## Current Focus

**v2.1 — Hybrid retrieval + trajectory ingest + downstream distribution.** Spec approved 2026-05-22; 4 open questions resolved per recommendations. Implementation split into 4 phases, 4 PRs. Ready to start Phase 1 (`feat/v2.1-phase-1-hybrid-retrieve`).

## Completed this session (2026-05-22)

- Deleted 8 local `feat/v2.0.0-phase-*` + `fix/v2.0.1-audit-followups` branches (locally + on origin) — v2.0.0/v2.0.1 archive now lives only in tags + main history.
- Removed `tmp_files.txt` debris.
- Verified v2.0.0 + v2.0.1 already pushed; both GitHub releases published; activeContext was stale.
- Wrote v2.1 spec: [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](../docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md). Updated `docs/specs/README.md` index.
- Resolved 4 open questions: Python `update_ecosystem.py` (not npx), expanded trajectory schema, hybrid as default retrieve mode, sparse-only fallback shipped.
- Rewrote `task.md` as v2.1 4-phase checklist.

## Sprint Goals (v2.1)

- [ ] Phase 1 — Hybrid retrieve (BM25 + dense + RRF fusion, `--mode` flag, sparse fallback) — branch `feat/v2.1-phase-1-hybrid-retrieve`
- [ ] Phase 2 — Trajectory ingest (expanded JSONL schema, dual-collection finalize) — branch `feat/v2.1-phase-2-trajectory-ingest`
- [ ] Phase 3 — Downstream distribution (`scripts/update_ecosystem.py`) — branch `feat/v2.1-phase-3-update-ecosystem`
- [ ] Phase 4 — Release v2.1.0 (CHANGELOG, version bump, tag, post-release audit ≥85)

## Blockers

None.

## Next Steps (start of next session)

1. Read this file + [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](../docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md) + `task.md`.
2. **First action:** commit the approved spec to `main`:
   - `git add docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md docs/specs/README.md task.md`
   - `git commit -m "docs(spec): v2.1 — hybrid retrieve + trajectory ingest + downstream distribution"`
   - Push.
3. Create `feat/v2.1-phase-1-hybrid-retrieve` off `main` and start Phase 1 per task.md.
4. Per Phase 1 checklist: add `rank-bm25` to `pyproject.toml::[project.optional-dependencies] reasoning`, implement `_bm25_retrieve` + `_rrf_fuse` in `scripts/reasoning_bank.py`, refactor `retrieve()` to dispatch on `mode`, add `--mode` + `--rrf-k` CLI flags, ensure sparse path works without chromadb.

## Resume context

- **Spec:** `docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md` — approved, 4 phases, 8–12 h.
- **Task list:** `task.md` — Phase 1 checklist active, all unchecked.
- **Model policy for this work:** Opus 4.7 default (per `.agents/rules/model-policy.md`); BM25 implementation is mechanical → safe to silently delegate to Sonnet subagent if context tightens.
