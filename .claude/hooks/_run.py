#!/usr/bin/env python3
"""Python launcher for Claude Code hooks — replaces the Bash _run.sh wrapper.

Resolves the right Python interpreter without requiring Git Bash on Windows.
Fallback chain:
  1. $CLAUDE_PROJECT_DIR/.venv/Scripts/python.exe  (Windows venv in project dir from env var)
  2. ./.venv/Scripts/python.exe                    (Windows venv relative)
  3. ./.venv/bin/python                            (POSIX venv relative)
  4. python3                                        (system, POSIX)
  5. python                                         (system, Windows/fallback)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_python() -> str:
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))

    candidates = [
        project_dir / ".venv" / "Scripts" / "python.exe",
        Path(".venv") / "Scripts" / "python.exe",
        Path(".venv") / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)

    for name in ("python3", "python"):
        found = shutil.which(name)
        if found:
            return found

    print("_run.py: Python not found (.venv or PATH)", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python .claude/hooks/_run.py <hook_script.py> [args...]", file=sys.stderr)
        sys.exit(1)

    python = _find_python()
    script = sys.argv[1]
    extra_args = sys.argv[2:]

    result = subprocess.run([python, script] + extra_args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
