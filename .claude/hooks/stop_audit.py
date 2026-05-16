#!/usr/bin/env python3
"""Stop hook: lightweight post-session audit.

Runs when Claude Code finishes a response. Checks:
- task.md — any unclosed `[ ]` or `[/]` items
- uncommitted git changes
- freshness of audit_history.jsonl (>14 days → suggest `/audit_ecosystem`)

Appends one entry to `.memory/audit_history.jsonl` (append-only JSONL)
for regression tracking across sessions.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
AUDIT_LOG = PROJECT_DIR / ".memory" / "audit_history.jsonl"


def check_task_md() -> list[str]:
    path = PROJECT_DIR / "task.md"
    if not path.exists():
        return []
    abandoned: list[str] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"\s*-\s*\[[ /]\]", line):
            abandoned.append(f"task.md:{i}: {line.strip()}")
    return abandoned


def count_uncommitted() -> int:
    try:
        out = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            cwd=str(PROJECT_DIR),
        )
    except (OSError, subprocess.TimeoutExpired):
        return -1
    return sum(1 for ln in (out.stdout or "").splitlines() if ln.strip())


def audit_age_days() -> int:
    """Returns age of the last entry in audit_history.jsonl (in days).

    Supports two timestamp formats: new (`timestamp`, UTC) and legacy (`date`, local).
    """
    if not AUDIT_LOG.exists():
        return 999
    try:
        last_line = AUDIT_LOG.read_text(encoding="utf-8").strip().splitlines()[-1]
        entry = json.loads(last_line)
        stamp = entry.get("timestamp") or entry.get("date")
        if not stamp:
            return 999
        last = dt.datetime.fromisoformat(stamp.rstrip("Z"))
        now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
        return (now - last).days
    except (OSError, IndexError, KeyError, ValueError):
        return 999


def main() -> int:
    notes: list[str] = []

    abandoned = check_task_md()
    if abandoned:
        notes.append(f"⚠️ {len(abandoned)} unclosed task(s) in task.md")

    uncommitted = count_uncommitted()
    if uncommitted > 0:
        notes.append(f"📝 {uncommitted} uncommitted change(s)")

    age = audit_age_days()
    if age > 14:
        notes.append(f"📊 audit_history.jsonl is {age} days old (run `/audit_ecosystem`)")

    # Always log (append-only) for session history
    entry = {
        "timestamp": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "stop_hook",
        "task_md_open": len(abandoned),
        "uncommitted": uncommitted,
        "audit_age_days": age,
    }
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging is best-effort

    if notes:
        print("## 🔔 Reminders (stop-hook):")
        for n in notes:
            print(f"- {n}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
