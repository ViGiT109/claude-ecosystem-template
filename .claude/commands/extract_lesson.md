---
description: Extract a lesson from an error and record it in .memory/lessons.md (ReasoningBank format)
---

# Extract Lesson from Error

This workflow activates when the agent (or user) discovers an error, bug, or anti-pattern that could recur.

> **Format:** Lessons are recorded in the structured ReasoningBank Memory Item format.

## Steps

### 1. Root Cause Analysis

Determine the root cause of the error:
- What happened?
- Why did it happen?
- Is this a systemic problem or a one-off?

### 2. Determine outcome

Evaluate the result of the session/task in which the error occurred:
- `success` — task completed, but a side-insight was discovered
- `partial-failure` — task completed, but with errors along the way
- `failure` — task not completed, or completed with critical problems

### 3. Classify

Determine the section in `lessons.md`:
- `Cross-Project` — universal error (applies to any project)
- `Project-Specific` — specific to this project
- `Anti-Patterns` — a prohibited behaviour pattern (add to the Anti-Patterns list)

### 4. Distil the strategy (ReasoningBank-style)

Formulate a Memory Item using the template:

**For SUCCESSFUL strategies (outcome: success):**
> You are an expert developer. You are given a session trajectory in which the agent **successfully** completed a task.
> Extract 1-3 reusable insights. Focus on generalizable patterns,
> do not mention specific files or values — principles only.

**For FAILED strategies (outcome: failure / partial-failure):**
> You are an expert developer. You are given a session trajectory in which the agent **failed** to complete a task or made errors.
> First analyse WHY the trajectory failed.
> Then extract 1-3 preventive lessons — strategies for avoiding similar errors in the future.

### 5. Record in lessons.md

Add the Memory Item to the appropriate section of `.memory/lessons.md`:

```markdown
### Memory Item: <short strategy name>
**Title:** <concise English strategy name>
**Description:** <one-sentence summary>
**Content:** <1-3 sentences with actionable insight. Root cause, fix, prevention.>
**Source:** session YYYY-MM-DD | outcome: <success|partial-failure|failure>
```

### 6. Evaluate severity

If the pattern has recurred 3+ times:
- Promote the rule to `.agents/rules/` (appropriate module)
- If it's an Anti-Pattern — add to the Anti-Patterns section in lessons.md

### 7. Sync with ChromaDB

After recording a new lesson in `lessons.md`, update the semantic index:
```bash
python scripts/reasoning_bank.py ingest_lessons
```
This ensures the new lesson is available via semantic search in `/new_session`.

> **Triggers:** "extract lesson", "record error", "lesson from bug", "don't repeat this", "learn from this"
