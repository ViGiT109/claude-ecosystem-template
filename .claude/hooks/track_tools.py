#!/usr/bin/env python3
"""PostToolUse hook: in-process tool-usage aggregator (v2.3 Phase 2).

Increments a per-session counter for the tool that just ran. The counter
state lives in `.memory/.session_tools.json` (ephemeral, gitignored). At
each Stop hook, `stop_audit.py` reads the counter for the current
session, writes a `tools_used` field into the `audit_history.jsonl`
entry, and clears the session's bucket.

Storage schema
--------------
::

    {
      "<session_id>": {
        "_updated": "2026-05-23T14:30:00Z",
        "tools": {"Bash": 3, "Read": 12, "Edit": 4}
      },
      ...
    }

Sessions not touched for 7 days are pruned by `stop_audit.py` to keep
the file bounded.

Concurrency
-----------
PostToolUse fires sequentially within a single Claude Code session (tools
run one at a time). Multiple concurrent sessions writing to the same file
are extremely rare; in that case the last writer wins and at most one
tool increment is lost. Acceptable for an audit-grade counter — we are
not billing on these numbers.

Input contract (Claude Code PostToolUse hook)
--------------------------------------------
::

    {
      "session_id": "...",
      "transcript_path": "...",
      "cwd": "...",
      "hook_event_name": "PostToolUse",
      "tool_name": "Bash",
      "tool_input": {...},
      "tool_response": {...}
    }

The hook is best-effort: malformed JSON, missing session_id, or any
write error returns 0 silently. Never block the tool pipeline.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
COUNTER_FILE = PROJECT_DIR / ".memory" / ".session_tools.json"


def _load() -> dict:
    if not COUNTER_FILE.is_file():
        return {}
    try:
        return json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save(data: dict) -> None:
    try:
        COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        COUNTER_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass  # best-effort


def main() -> int:
    # Dry-run path — used by `scripts/check_hook_health.py` to verify the
    # hook loads without import or syntax errors. Skip stdin reads + writes.
    if os.environ.get("HOOK_DRYRUN") == "1":
        return 0

    raw = sys.stdin.read()
    if not raw:
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    session_id = payload.get("session_id") or "_unknown"
    tool_name = payload.get("tool_name")
    if not tool_name:
        return 0

    data = _load()
    bucket = data.setdefault(session_id, {"_updated": "", "tools": {}})
    bucket["_updated"] = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    bucket["tools"][tool_name] = bucket["tools"].get(tool_name, 0) + 1
    _save(data)

    return 0


if __name__ == "__main__":
    sys.exit(main())
