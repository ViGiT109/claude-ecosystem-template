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
import re
import sys

# matches: `git commit --no-verify`, `git commit ... --no-verify`,
#          `git commit -n`, `git commit -abcn` (short flags without --)
NO_VERIFY_RE = re.compile(
    r"\bgit\s+commit\b[^\n]*?(--no-verify|(?<![A-Za-z\-])-[A-Za-z]*n(?![A-Za-z]))",
)


def main() -> int:
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
            "ЗАБЛОКИРОВАНО хуком .claude/hooks/block_no_verify.py:\n"
            "  Команда использует --no-verify (или -n), что запрещено CLAUDE.md.\n"
            "  Pre-commit хуки — часть guardrails проекта (task.md, линтинг, deps-sync).\n"
            "  Если pre-commit хук сломан — СНАЧАЛА почини его, потом коммить.",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
