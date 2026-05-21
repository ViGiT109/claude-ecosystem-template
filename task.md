# Task: v2.0.0 Phase 5 — ReasoningBank auto-ingest (PR #5)

**Branch:** `feat/v2.0.0-phase-5-reasoning-bank-ingest` (stacked on Phase 4)
**Spec:** [docs/specs/2026-05-21-production-readiness.md](docs/specs/2026-05-21-production-readiness.md) §Phase 5
**Acceptance #7:** «Финализация сессии триггерит ReasoningBank ingest; статус в `.memory/audit_history.jsonl`».
**Goal:** add a non-blocking, timeout-bound subprocess call from `finalize_session.py` into `scripts/reasoning_bank.py ingest_lessons`, with structured status logged to `audit_history.jsonl`.

## Legend
- `[ ]` — not started (blocks commit)
- `[/]` — in progress (blocks commit)
- `[x]` — completed
- `[-]` — skipped / not applicable

## Execution pattern
Pure Sonnet-class work — single file, small surface area, mechanical. Main thread (Opus 4.7) handles it inline; no subagent delegation needed.

## Steps

### 5.1 — Patch `scripts/finalize_session.py`
- [x] Add module-level constant `AUDIT_HISTORY_FILE = ".memory/audit_history.jsonl"`
- [x] Add `ingest_reasoning_bank()` — non-blocking subprocess call to `python scripts/reasoning_bank.py ingest_lessons` with `timeout=30`, `check=False`, `capture_output=True`, `text=True`
- [x] Handle exceptions: `subprocess.TimeoutExpired` → status `"timeout"`; other `OSError`/`Exception` → status `"error"` with message
- [x] Map returncode: `0` → `"ok"`; non-zero → `"skipped"` (ChromaDB missing is the common case — not a failure)
- [x] Capture last ~5 lines of stdout/stderr (truncated) for diagnostics
- [x] Append one JSON line to `.memory/audit_history.jsonl` with: `event: "reasoning_bank_ingest"`, `timestamp` (ISO UTC), `status`, `returncode`, `duration_s`, `stdout_tail`, `stderr_tail`
- [x] Print a one-line human-readable summary (e.g. `📚 ReasoningBank ingest: ok (12 lessons, 1.3s)` or `📚 ReasoningBank ingest: skipped — chromadb not installed`)
- [x] Wire into `main()` between `collect_session_metrics()` and `record_session_trajectory()`
- [x] Confirm script keeps working when `.memory/audit_history.jsonl` doesn't yet exist (open append mode creates it)

### 5.2 — Smoke test: chromadb-missing path (current env)
- [x] Run `python -c "from scripts.finalize_session import ingest_reasoning_bank; ingest_reasoning_bank()"` (or equivalent direct invocation)
- [x] Verify `audit_history.jsonl` gains a row with `event: "reasoning_bank_ingest"` and `status: "skipped"` (or `"error"` if missing-module bubbles up via stderr)
- [x] Verify the call returns normally — no SystemExit, no traceback in the parent

### 5.3 — Code-path review: timeout & error branches
- [x] Trace the `subprocess.TimeoutExpired` branch — confirm the JSON row is still written and the function returns
- [x] Trace the generic `Exception` branch — confirm we never let an exception escape into `finalize_session.main()`

### 5.4 — Manifest & sync sanity
- [x] `python scripts/regenerate_plugin_manifest.py --check` → exit 0 (no hooks/skills/commands changed, expect clean)
- [x] `python scripts/sync_agents_md.py --check` → exit 0 (no AGENTS.md changes — pure script edit)

### 5.5 — Wrap-up
- [x] Update `.memory/activeContext.md` — Phase 5 complete, Phase 6 next
- [x] Commit `feat(reasoning-bank): v2.0.0 Phase 5 — auto-ingest on session finalize` (NO `--no-verify`)

## Non-goals (this PR)
- Hybrid search (BM25 + vector) in `reasoning_bank.py` — explicitly out of scope (v2.1+)
- Ingesting trajectories alongside lessons — keep this PR minimal; trajectories ingest is already a separate command
- New subagents, statusline, pyproject scaffold — Phase 6

## Acceptance
- `scripts/finalize_session.py` runs ReasoningBank ingest as a bounded subprocess and always logs a structured row to `.memory/audit_history.jsonl`
- When `chromadb` is absent the function reports `skipped` and finalize_session keeps going
- No new pre-commit failures; manifest + AGENTS.md sync stay green
