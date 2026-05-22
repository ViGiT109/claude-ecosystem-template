# Lessons Learned — Agent Error Journal

> **Self-Improvement Loop:** This file is automatically read at every `/new_session`.
> The agent must account for these lessons and not repeat documented errors.
> To add a new lesson — use the `/extract_lesson` workflow.

> **Format (ReasoningBank v1):** Each lesson is a structured Memory Item.
> Structure: Title / Description / Content / Source.

---

## Cross-Project (universal)

### Memory Item: Never read large files in full
**Title:** Large file reading prevention
**Description:** Log files and runtime data can be megabytes — always read only the tail.
**Content:** Use `Get-Content -Tail 100/200` (PowerShell) or `tail -n 200` (POSIX). Reading a large runtime file in full causes context overflow and loss of working memory.
**Source:** template baseline | outcome: prevention

### Memory Item: Close tasks in task.md continuously
**Title:** Continuous task.md completion
**Description:** Prompt drift during long operations leads to abandoned tasks.
**Content:** During long sessions the agent tends to forget updating task.md, leaving `[ ]` / `[/]` items. The pre-commit guardrail blocks commits when unchecked tasks exist. Mark each step `[x]` immediately upon completion — not at the end of the session.
**Source:** template baseline | outcome: prevention

---

## Project-Specific

### Memory Item: Append-only logs need event-type filters for "freshness" checks
**Title:** Don't measure freshness by mtime or last-line on a write-heavy log
**Description:** A freshness/staleness signal on an append-only JSONL log is meaningless when the file is written by a high-frequency event (e.g. every Claude turn). Using file mtime or `lines[-1]` masks the actual age of the signal the user cares about.
**Content:** `.memory/audit_history.jsonl` is appended to by `stop_audit.py` on every Stop hook (`event: "stop_hook"`) — once per Claude turn. The original `audit_age_days()` (in `stop_audit.py`) and `check_audit_debt()` (in `finalize_session.py`) reported the age of the **last entry** or the **file mtime**, both of which were always seconds old. Result: a "no full audit in N days" signal that could never fire. **Fix:** always filter by the specific `event` type you care about (`event == "audit_complete"`) and find the most recent qualifying entry; never use file mtime as a proxy for "did this specific thing happen recently". Producers of those events must explicitly emit them — `/audit_ecosystem` Phase E now appends the `audit_complete` marker.
**Source:** Phase 2 PR #2, 2026-05-21 | outcome: prevention + fix applied

### Memory Item: Don't outsource contextual signals to deterministic hooks
**Title:** Emit PLAN/MODEL block manually when triggers are contextual, not lexical
**Description:** `planning_hint.py` (UserPromptSubmit) fires only on RU/EN keyword triggers or ≥3 file references — by design. When the user prompt is short ("делаем всё по порядку", "продолжаем", "делай") but the underlying work is architectural (writing a multi-phase spec, designing a subsystem, scoping a release), the hook stays silent. AGENTS.md explicitly requires the agent to close that gap by hand; relying on the hook alone causes silent drift from the planning/model policy.
**Content:** **Root cause:** the agent treats `planning_hint.py` as a complete planning detector instead of a lexical-only first line. **Prevention:** before invoking `/create_spec`, `/agentic_tdd`, or any design-skill — and before any work spanning >1 phase or >3 files — verify that the `🧭 PLAN + 💡 MODEL` block was emitted (either by the hook earlier in the turn, or by me inline). If not, emit it before the skill call. The block format is in `.agents/rules/model-policy.md` §Block formats. Cost of emitting one is near-zero; cost of omitting one is policy drift the user has to catch.
**Source:** session 2026-05-22 (v2.1 spec creation) | outcome: partial-failure (spec written correctly, but signal block skipped)

### Memory Item: Ship code paths with at least one prod run before declaring DONE
**Title:** Write-path features must have a real production write before release
**Description:** v2.1.0 Phase 2 shipped a rewritten `record_session_trajectory()` and the dual-collection ingest pipeline. Both passed smoke tests in isolation, but `.memory/session_trajectories.jsonl` stayed at 0 bytes for the entire sprint — no real session finalization ever ran the code path. The v2.1.0 post-release audit caught it (`audit_v2.1.0_release.md` §Scorecard row 12).
**Content:** **Acceptance criterion for any write-path feature** (logger, ingest, journal, recorder): a real entry in the actual sink file must exist BEFORE the release commit. Smoke tests inside `if __name__ == "__main__"` don't count — they write to temp or in-memory. **Concrete checks:** (a) `wc -l <sink-file>` must increase between sprint start and release, OR (b) a pre-release script invokes the function on a fixture and asserts the file changed. v2.1.1 added a one-shot smoke-call to `record_session_trajectory()` directly before tagging — that's the minimum bar. **Promotion path:** if this trips a second time → encode as a pre-tag guardrail that diffs sink files against sprint-start mtime/size.
**Source:** v2.1.0 post-release audit, 2026-05-23 | outcome: prevention + fix applied in v2.1.1

### Memory Item: Single-source-of-truth for project version (and verify on release)
**Title:** Version lives in plugin.json; everywhere else reads or mirrors it
**Description:** v2.1.0 released with `plugin.json` bumped to 2.1.0 and CHANGELOG §[2.1.0] written, but `.ecosystem.toml` had no `[ecosystem]` section at all — neither `version` nor `file_shas`. The spec L62 and `activeContext.md:26` both required bumping `.ecosystem.toml` too. Worse, `update_ecosystem.py::get_upstream_version()` was looking for `plugin.json` at the repo root, while the real file lives at `.claude-plugin/plugin.json` — so even a manual `--apply` would have skipped the version field. Two failures stacked: missing release step + path bug.
**Content:** **Rule:** `plugin.json` is the source-of-truth version. `.ecosystem.toml` mirrors it (written by `update_ecosystem.py --apply` from upstream `plugin.json`). CHANGELOG header `## [X.Y.Z]` and git tag `vX.Y.Z` must match. **Prevention layers** (in order of cost):
1. **Release checklist in `task.md`** — explicit checkboxes for each of {plugin.json, .ecosystem.toml, CHANGELOG, tag}. Pre-commit guardrail then forces them closed.
2. **Pre-tag guardrail** — `git push --tags` should fail if `plugin.json:version` ≠ tag suffix ≠ last CHANGELOG `## [X.Y.Z]`. Add when bug recurs.
3. **`update_ecosystem.py` correctness** — keep `get_upstream_version()` aware of both `.claude-plugin/plugin.json` (current Claude Code layout) and root `plugin.json` (legacy). Don't assume one location.
**Source:** v2.1.0 post-release audit, 2026-05-23 | outcome: prevention + path bug fixed in v2.1.1

### Memory Item: Release phase checkboxes belong in task.md, not activeContext.md
**Title:** Release phase tracked in task.md, not in activeContext.md
**Description:** In v2.1.0 `task.md` had explicit checkboxes for Phase 1/2/3 but Phase 4 (release) was only a prose section. The "Phase 4 — Release v2.1.0" checkbox lived in `activeContext.md:21`. Pre-commit guardrail (`scripts/check_task_guardrail.py`) only scans `task.md`, so release-phase state was never gated by the guardrail. Caught in v2.1.0 post-release audit (Scorecard row 3).
**Content:** When opening any sprint `task.md`, include an explicit `## Phase N — Release` section with checkboxes for: CHANGELOG update, version bump in each tracked file, annotated tag, post-release audit ≥ target. Closing each `[x]` simultaneously: (a) records the release event, (b) keeps tracking in one place, (c) gives the pre-commit guardrail something it can actually block on. Don't split release-phase state across `activeContext.md` and `task.md` — `activeContext.md` is for narrative, `task.md` is for guardrail-readable state.
**Source:** v2.1.0 post-release audit, 2026-05-23 | outcome: prevention + applied in v2.1.1 task.md

---

## Anti-Patterns

<!-- Patterns that have recurred 3+ times and are now hard rules -->
<!-- Also add to .agents/rules/ when promoting an anti-pattern -->
