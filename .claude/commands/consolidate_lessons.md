---
description: Consolidate .memory/ files — merge duplicates, fix stale facts, prune the lessons index. Writes a `consolidate_complete` event afterwards.
model: opus
---

# Consolidate memory

Run a reflective pass over the project's memory files in `.memory/`
(specifically `lessons.md`, `activeContext.md`, `progress.md`,
`systemPatterns.md`, `techContext.md`) and clean them up:

- Merge duplicate lessons / facts.
- Fix stale information (anything contradicted by the current codebase).
- Prune lessons that are no longer relevant (no longer reachable from current rules / patterns).
- Reorganise sections if the file has drifted from the documented format.

## Steps

### 1. Invoke the consolidate-memory skill

Use the `anthropic-skills:consolidate-memory` skill. It is the canonical
reflective-consolidation pass. The skill handles the dedup / merge /
prune logic — do not reimplement.

### 2. Verify the result

After the skill finishes:
- Check `.memory/lessons.md` still parses (each `### Memory Item:`
  block has Title/Description/Content/Source).
- Confirm no important lesson was dropped (cross-check against the
  v2.1.0 / v2.1.1 lessons that established the current rules).
- If anything looks wrong — revert with `git checkout .memory/`.

### 3. Record the event

Append a `consolidate_complete` row to `.memory/audit_history.jsonl`
so that `session_start.py` can stop emitting the
🟡 `CONSOLIDATE RECOMMENDED` marker on next session start (Phase 4 of
v2.2 self-diagnostic sprint).

Run this one-liner from the project root (don't forget `lessons_before`
and `lessons_after` counts — count `### Memory Item:` headers in
`.memory/lessons.md` before and after the skill):

```bash
python -c "
import datetime, json, pathlib
entry = {
    'timestamp': datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'event': 'consolidate_complete',
    'lessons_before': BEFORE,
    'lessons_after': AFTER,
    'source': 'skill'
}
with pathlib.Path('.memory/audit_history.jsonl').open('a', encoding='utf-8') as f:
    f.write(json.dumps(entry) + '\n')
print('✅ consolidate_complete event recorded')
"
```

Replace `BEFORE` and `AFTER` with the actual counts.

### 4. Commit

`/commit_and_release` — short message `chore(memory): consolidate lessons.md (Nb→Na)`.
