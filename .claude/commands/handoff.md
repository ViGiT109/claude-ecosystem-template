---
description: Prepare for session handoff — update activeContext.md with resume notes, suggest a commit, emit resume instructions for the next session
model: inherit
---

# Session Handoff

Execute these steps in order without pausing for confirmation.

## Step 1 — Capture current state

```bash
git status --short
git log --oneline -5
```

Note: uncommitted file count, last commit SHA and message.

## Step 2 — Read active task (if it exists)

Read `task.md` if present. Note which items are `[x]` (done) and which are `[ ]` or `[/]` (pending).

## Step 3 — Read active context

Read `.memory/activeContext.md` — current sprint focus and last known state.

## Step 4 — Update `.memory/activeContext.md`

Rewrite (or append to) the file with:

- **Date:** today's date (YYYY-MM-DD)
- **Completed this session:** bullet list of what was done
- **Current sprint focus:** one sentence — what the work is building toward
- **Blockers:** any known blockers (or "none")
- **Next Steps:** concrete instructions for the next session — file names, task IDs,
  commands to run first. Write as if telling a stranger exactly where to pick up.

Keep it under 40 lines. Overwrite stale content; do not accumulate past dates.

## Step 5 — Suggest a commit (if uncommitted changes exist)

If `git status` from Step 1 shows dirty files:

```
Suggested commit message:
  chore(state-sync): session handoff — <one-phrase summary of changes>
```

Do NOT run `git commit`. The user decides.

## Step 6 — Emit handoff block

```
🔄 SESSION HANDOFF RECOMMENDED
   Context: <pct>% of <window> — switching models won't reclaim space
   Suggested action: /handoff → new session → /new_session
```

Fill `<pct>` and `<window>` from your estimate of current context consumption.

## Step 7 — Print resume instructions

```
In your next session, run `/new_session` and say:
  "continue <topic from activeContext> — last worked on <YYYY-MM-DD>"
```

Replace `<topic>` with the sprint focus you wrote in Step 4.
