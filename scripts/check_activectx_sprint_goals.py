#!/usr/bin/env python3
"""activeContext.md Sprint Goals desync guardrail (v2.3 Phase 1).

Promoted from lesson `.memory/lessons.md::activeContext.md Sprint Goals desync`,
which recurred in v2.1.1 and v2.2.0 post-release audits. Per the upgrade-path
in CLAUDE.md (`lesson → rule → guardrail`), a 2nd recurrence promotes the
observation to a deterministic hook.

What it does
------------
When a commit changes the `version` field of `.claude-plugin/plugin.json`
(i.e. a release-bump commit), the script scans `.memory/activeContext.md`
inside any heading whose text contains "Sprint Goals" and blocks the commit
if any unchecked `- [ ]` or in-progress `- [/]` checkbox remains. The Sprint
Goals state must mirror `task.md` at every release.

When it stays silent
--------------------
- `.claude-plugin/plugin.json` not in the staged diff → exit 0.
- Plugin manifest staged but `version` field unchanged (e.g. file-list refresh
  via `regenerate_plugin_manifest.py`) → exit 0.
- No `.memory/activeContext.md` file → exit 0 (project not bootstrapped yet).
- `## Sprint Goals` (or any header containing those words) absent → exit 0.

Exit codes
----------
0 — pass (no release bump, or all Sprint Goals checkboxes are `[x]`).
1 — block (release bump detected AND unchecked Sprint Goals checkbox found).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PLUGIN_JSON = ".claude-plugin/plugin.json"
ACTIVECTX = ".memory/activeContext.md"


def staged_diff(path: str) -> str:
    """Return `git diff --cached -- <path>` output, or empty string on error."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--", path],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout
    except (FileNotFoundError, OSError):
        return ""


def version_bumped(diff: str) -> bool:
    """Detect whether the staged plugin.json diff changes the `version` field."""
    return bool(re.search(r'^\+\s*"version"\s*:', diff, re.MULTILINE))


def find_unchecked_sprint_items(path: Path) -> list[tuple[int, str]]:
    """Return list of (lineno, line) under any ## heading containing 'Sprint Goals'."""
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    found: list[tuple[int, str]] = []
    inside_sprint_section = False

    for idx, raw in enumerate(lines, 1):
        # Section transitions are signalled by ATX headings.
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", raw)
        if heading_match:
            heading_text = heading_match.group(2).strip().lower()
            inside_sprint_section = "sprint goals" in heading_text
            continue

        if not inside_sprint_section:
            continue

        # Unchecked or in-progress checkbox at the start of a list item.
        if re.match(r"\s*-\s*\[[ /]\]", raw):
            found.append((idx, raw.rstrip()))

    return found


def main() -> int:
    # Run from repo root regardless of caller cwd.
    repo_root = Path(__file__).resolve().parent.parent

    diff = staged_diff(PLUGIN_JSON)
    if not diff:
        # plugin.json not staged → not a release-bump commit by our heuristic.
        return 0

    if not version_bumped(diff):
        # plugin.json changed but version line untouched (e.g. file-list refresh).
        return 0

    active_path = repo_root / ACTIVECTX
    unchecked = find_unchecked_sprint_items(active_path)
    if not unchecked:
        return 0

    print("❌ activeContext.md Sprint Goals DESYNC — release commit blocked!")
    print(f"   release-bump detected in {PLUGIN_JSON} but {ACTIVECTX} still has")
    print("   unchecked Sprint Goals:")
    for lineno, line in unchecked:
        print(f"     {ACTIVECTX}:{lineno}: {line}")
    print()
    print("Fix: mark every Sprint Goals checkbox `[x]` or remove the section")
    print("entirely if the sprint is closed, then re-stage activeContext.md.")
    print()
    print("Rule reference: .agents/rules/git.md § Release Workflow")
    print("Promoted from lesson: .memory/lessons.md (v2.1.1 + v2.2.0 audits)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
