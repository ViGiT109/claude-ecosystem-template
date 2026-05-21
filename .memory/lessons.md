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

---

## Anti-Patterns

<!-- Patterns that have recurred 3+ times and are now hard rules -->
<!-- Also add to .agents/rules/ when promoting an anti-pattern -->
