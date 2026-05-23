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

# Local sibling import — `_ecosystem_health.py` is in the same directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ecosystem_health import audit_age_days  # noqa: E402

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
AUDIT_LOG = PROJECT_DIR / ".memory" / "audit_history.jsonl"
SESSION_TOOLS = PROJECT_DIR / ".memory" / ".session_tools.json"
SESSION_TOOLS_TTL_DAYS = 7


def check_task_md() -> list[str]:
    path = PROJECT_DIR / "task.md"
    if not path.exists():
        return []
    abandoned: list[str] = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"\s*-\s*\[[ /]\]", line):
            abandoned.append(f"task.md:{i}: {line.strip()}")
    return abandoned


def consume_session_tools(session_id: str | None) -> dict[str, int]:
    """Read tool-usage counter for this session, clear it, prune stale buckets.

    Returns the per-tool count dict (`{tool_name: count}`) accumulated since
    the last Stop hook for this session. Returns `{}` on any IO/parse error or
    when no bucket exists (sessions with zero tool calls).

    Stale buckets (`_updated` older than SESSION_TOOLS_TTL_DAYS) are GC'd in
    the same write so the file stays bounded even if Stop never fires for
    some crashed session.
    """
    if not SESSION_TOOLS.is_file():
        return {}
    try:
        data = json.loads(SESSION_TOOLS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}

    # Pop current session's bucket.
    bucket = data.pop(session_id, None) if session_id else None
    tools = bucket.get("tools", {}) if isinstance(bucket, dict) else {}

    # GC stale buckets (best-effort; ignore malformed entries).
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=SESSION_TOOLS_TTL_DAYS)
    for sid in list(data.keys()):
        entry = data.get(sid)
        if not isinstance(entry, dict):
            data.pop(sid, None)
            continue
        ts = entry.get("_updated") or ""
        try:
            when = dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.UTC)
        except ValueError:
            data.pop(sid, None)
            continue
        if when < cutoff:
            data.pop(sid, None)

    try:
        SESSION_TOOLS.parent.mkdir(parents=True, exist_ok=True)
        SESSION_TOOLS.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass  # best-effort; data already captured for the entry

    return tools if isinstance(tools, dict) else {}


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


def main() -> int:
    # Dry-run mode — used by `scripts/check_hook_health.py` to verify the hook
    # loads without import/syntax errors. Skips audit_history.jsonl write and
    # stdout reminder output.
    if os.environ.get("HOOK_DRYRUN") == "1":
        return 0

    # Best-effort stdin parse — Claude Code passes a JSON payload with
    # `session_id`, `transcript_path`, `stop_hook_active`. Used here only to
    # pick the matching bucket from `.session_tools.json`. Tolerate missing
    # stdin entirely (e.g. manual invocation).
    session_id: str | None = None
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        if raw:
            payload = json.loads(raw)
            sid = payload.get("session_id")
            if isinstance(sid, str) and sid:
                session_id = sid
    except (json.JSONDecodeError, OSError, ValueError):
        pass

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

    tools_used = consume_session_tools(session_id)

    # Always log (append-only) for session history
    entry = {
        "timestamp": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "stop_hook",
        "task_md_open": len(abandoned),
        "uncommitted": uncommitted,
        "audit_age_days": age,
        "tools_used": tools_used,
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
