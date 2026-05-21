---
description: Start a new project session with Progressive Context Loading
model: inherit
---

# New Session — Progressive Context Loading

Run this at the beginning of every new conversation to load the right context.

> **CLAUDE.md** is picked up by Claude Code automatically. This command loads the rest.
> **Principle:** Progressive Disclosure — load the minimum upfront, the rest on demand.

## 🔴 ALWAYS (required every session)

0. **Self-Improvement Loop — load relevant lessons:**
```
Run: python scripts/reasoning_bank.py retrieve "<current focus from activeContext.md>" --top-k 5
Read only the returned lessons — these are the Top-5 semantically closest to the current task.
Fallback: if ChromaDB is unavailable or empty — read `.memory/lessons.md` in full.
DO NOT REPEAT documented anti-patterns!
```

1. **Active context:**
```
Read `.memory/activeContext.md` — current task focus.
```

2. **Recent commits (git):**
```
Run `git log --oneline -10` and `git status` — see where we left off.
```

## 🟡 AUTO (load only when the task is related)

3. **Rules** — load only what's relevant:
   - Git operations, releases → `.agents/rules/git.md`
   - Writing new code → `.agents/context/coding-conventions.md`
   - Dependencies → `.memory/techContext.md`

4. **Recurring error patterns** — `.memory/lessons.md` (if not loaded via ReasoningBank).

## 🟢 ON-DEMAND (load only when explicitly needed)

- `.memory/projectbrief.md` — project overview (new sessions, architecture)
- `.memory/systemPatterns.md` — before architectural decisions
- `.memory/progress.md` — when asking about progress
- `ROADMAP.md` — when planning
- `docs/adr/`, `docs/specs/` — before large changes

## Session start wrap-up

5. **Summarise context for the user:**
   - Current task focus (from activeContext.md)
   - Any uncommitted changes
   - Key lessons from lessons.md (if relevant)
   - Ask: "What are we working on today?"

6. **Agentic Context Loader Guardrail:**
> After receiving the task from the user, assess its complexity.
> If the task requires more than one step — you **MUST** create `task.md`
> (or use Plan mode in Claude Code).
> Ad-hoc coding without a plan is prohibited for complex tasks.
