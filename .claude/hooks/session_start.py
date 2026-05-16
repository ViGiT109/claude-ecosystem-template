#!/usr/bin/env python3
"""SessionStart hook: injects current project focus into Claude's context.

Outputs:
- First lines of `.memory/activeContext.md` (current phase, sprint focus)
- Freshness of `.memory/lessons.md` (last-updated date)
- Uncommitted git changes status

The stdout of this script is automatically injected into the Claude Code session context.
"""
from __future__ import annotations

import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))


def emit_active_context() -> None:
    path = PROJECT_DIR / ".memory" / "activeContext.md"
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    # First 25 lines typically contain YAML frontmatter + current phase
    head = "\n".join(lines[:25]).rstrip()
    if head:
        print("## 📍 activeContext.md (sprint focus)")
        print(head)
        print()


def emit_lessons_freshness() -> None:
    path = PROJECT_DIR / ".memory" / "lessons.md"
    if not path.exists():
        return
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime)
    age_days = (dt.datetime.now() - mtime).days
    if age_days < 7:
        status = "🟢 fresh"
    elif age_days < 30:
        status = "🟡 getting stale"
    else:
        status = "🔴 overdue for update"
    print(f"## 📚 lessons.md: {status} (updated {age_days} days ago — {mtime:%Y-%m-%d})")
    print()


def emit_git_status() -> None:
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
        return
    lines = [ln for ln in (out.stdout or "").splitlines() if ln.strip()]
    if not lines:
        print("## 🧹 git: clean (no uncommitted changes)")
    else:
        print(f"## ⚠️ git: {len(lines)} uncommitted change(s)")
        for ln in lines[:10]:
            print(f"  {ln}")
        if len(lines) > 10:
            print(f"  ... and {len(lines) - 10} more")
    print()


def main() -> int:
    print("# 🚀 Project context (auto-injected by SessionStart hook)")
    print()
    emit_active_context()
    emit_lessons_freshness()
    emit_git_status()
    print("_Run `/new_session` to load full context._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
