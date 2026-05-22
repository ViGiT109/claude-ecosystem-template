#!/usr/bin/env python3
"""PreToolUse hook: blocks `git commit --no-verify` and `git commit -n`.

CLAUDE.md explicitly prohibits bypassing pre-commit guardrails. This hook makes
the prohibition deterministic (not based on prompt compliance alone).

Hook protocol (Claude Code):
- reads JSON from stdin (`tool_input.command` — the command Claude wants to run)
- exit 0 → allow
- exit 2 → block (stderr goes into Claude's context)
"""
from __future__ import annotations

import json
import os
import re
import sys

# matches: `git commit --no-verify`, `git commit ... --no-verify`,
#          `git commit -n`, `git commit -abcn` (short flags without --)
NO_VERIFY_RE = re.compile(
    r"\bgit\s+commit\b[^\n]*?(--no-verify|(?<![A-Za-z\-])-[A-Za-z]*n(?![A-Za-z]))",
)


def main() -> int:
    # Dry-run mode — used by `scripts/check_hook_health.py`.
    if os.environ.get("HOOK_DRYRUN") == "1":
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Empty or malformed input — don't block, let Claude Code handle it
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if NO_VERIFY_RE.search(command):
        print(
            "BLOCKED by .claude/hooks/block_no_verify.py:\n"
            "  Command uses --no-verify (or -n), which is prohibited by CLAUDE.md.\n"
            "  Pre-commit hooks are part of the project guardrails (task.md, linting, deps-sync).\n"
            "  If a pre-commit hook is broken — FIX IT FIRST, then commit.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
