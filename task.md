# Task: v2.1 — Hybrid Retrieval + Trajectory Ingest + Downstream Distribution

**Spec:** [docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md](docs/specs/2026-05-22-v2.1-reasoning-bank-distribution.md)
**Status:** Phase 1 complete (this PR). Phases 2–4 tracked in spec + activeContext sprint goals.
**Estimated remaining:** 5–8 h across 3 phases.

## Phase 1 — Hybrid retrieve (`feat/v2.1-phase-1-hybrid-retrieve`) — **DONE**

- [x] Add `rank-bm25` to `pyproject.toml::[project.optional-dependencies] reasoning` (also created the `pyproject.toml` itself — first one in repo)
- [x] Implement `_bm25_retrieve(query, top_k)` in `reasoning_bank.py` — parses lessons.md / trajectories.jsonl, builds BM25Okapi, `lru_cache` keyed on path + mtime_ns
- [x] Implement `_rrf_fuse(dense_results, sparse_results, k=60)` — Reciprocal Rank Fusion merge with per-item `_sources` annotation
- [x] Refactor `retrieve()` to dispatch on `mode ∈ {dense, sparse, hybrid}` (default: `hybrid`); over-fetch `top_k*4` per ranker before fusion
- [x] CLI: `--mode` and `--rrf-k` flags; `sparse` path never imports chromadb; `hybrid` degrades silently to sparse if chromadb missing; `dense` exits with friendly error
- [x] `mode` field logged in `.memory/retrieval_logs.jsonl`
- [x] Query-harness test `scripts/test_reasoning_bank.py` — 5 assertions covering exact-token, paraphrase, multilingual (Cyrillic), and hybrid-degradation. All pass.
- [x] Commit, push, verify pre-commit clean

## Remaining phases (see spec)

- **Phase 2** — Trajectory ingest (`feat/v2.1-phase-2-trajectory-ingest`): expanded JSONL schema in `record_session_trajectory()`, dual-collection finalize, two `audit_history.jsonl` rows.
- **Phase 3** — Downstream distribution (`feat/v2.1-phase-3-update-ecosystem`): new `scripts/update_ecosystem.py` with `--dry-run` default, SHA-protected `CLAUDE.md`/`AGENTS.md`, skiplist for `.memory/` and `.env*`.
- **Phase 4** — Release (`release/v2.1.0`): version bump in `plugin.json` + `.ecosystem.toml`, CHANGELOG v2.1 entry, annotated tag, post-release audit ≥85/100.

## Side branch (independent of phases)

- **`chore/ru-user-facing-and-language-hook`** — переведены `.memory/activeContext.md`, `.memory/lessons.md`, сообщения хуков (`session_start.py`, `planning_hint.py`, `stop_audit.py`, `block_no_verify.py`) и `scripts/check_task_guardrail.py`; добавлен новый хук `.claude/hooks/language_check.py` (UserPromptSubmit, детектит кириллицу → инжектит напоминание отвечать по-русски). Зарегистрирован в `.claude/settings.json`, `plugin.json` регенерирован. Англоязычные артефакты шаблона (`AGENTS.md`, `CLAUDE.md`, `TEMPLATE_README.md`, `.agents/rules/*`) сознательно не трогали — кросс-инструментальный стандарт.

Acceptance criteria for all phases are mirrored in the spec; sprint progress is tracked in [.memory/activeContext.md](.memory/activeContext.md).
