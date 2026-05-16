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

<!-- Add project-specific lessons here using /extract_lesson -->

---

## Anti-Patterns

<!-- Patterns that have recurred 3+ times and are now hard rules -->
<!-- Also add to .agents/rules/ when promoting an anti-pattern -->
