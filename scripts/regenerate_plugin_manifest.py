#!/usr/bin/env python3
"""Regenerate `.claude-plugin/plugin.json` from the actual contents of `.claude/`.

The plugin manifest must list every file the plugin ships. Doing this by hand
guarantees drift the moment someone adds a slash-command or skill. This script
scans the canonical locations and rewrites the `files` array deterministically.

Inputs scanned (every match becomes one entry):
  - `.claude/hooks/*.py`
  - `.claude/commands/*.md`
  - `.claude/agents/*.md`
  - `.claude/skills/*/SKILL.md`

All other fields in `plugin.json` (name, version, description, etc.) are
preserved verbatim.

Modes:
  --write    : (default) overwrite `.claude-plugin/plugin.json`
  --stdout   : print the regenerated manifest to stdout; touch nothing
  --check    : exit 1 with a diff when the on-disk manifest is stale.
               Used by the `plugin-manifest-sync` pre-commit hook.

Exit codes:
  0  success
  1  drift detected in --check mode, or write failed
  2  source layout invalid (`.claude/` missing, plugin.json missing)
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_DIR / ".claude-plugin" / "plugin.json"
CLAUDE_DIR = PROJECT_DIR / ".claude"


def discover_files() -> list[str]:
    """Return the sorted, posix-style list of files the plugin should ship."""
    if not CLAUDE_DIR.is_dir():
        print(f"❌ {CLAUDE_DIR.relative_to(PROJECT_DIR)} not found", file=sys.stderr)
        sys.exit(2)

    found: set[Path] = set()
    found.update((CLAUDE_DIR / "hooks").glob("*.py"))
    found.update((CLAUDE_DIR / "commands").glob("*.md"))
    found.update((CLAUDE_DIR / "agents").glob("*.md"))
    # Each skill is a directory containing SKILL.md (other support files in the
    # skill dir are shipped implicitly by virtue of the directory — only the
    # entry-point file needs to be listed).
    for skill_md in (CLAUDE_DIR / "skills").glob("*/SKILL.md"):
        found.add(skill_md)

    # Convert to repo-relative posix paths, dedupe, sort for determinism.
    rels = sorted(
        path.relative_to(PROJECT_DIR).as_posix() for path in found
    )
    return rels


def build_manifest() -> str:
    """Return the regenerated manifest as a JSON string (2-space indent, trailing newline)."""
    if not MANIFEST.exists():
        print(f"❌ {MANIFEST.relative_to(PROJECT_DIR)} not found — create it first", file=sys.stderr)
        sys.exit(2)
    try:
        current = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"❌ {MANIFEST.relative_to(PROJECT_DIR)} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    current["files"] = discover_files()
    # `json.dumps` with indent=2 + trailing newline → matches what an editor on
    # save-on-write would produce and stays diff-friendly.
    return json.dumps(current, indent=2, ensure_ascii=False) + "\n"


def cmd_write(content: str) -> int:
    MANIFEST.write_text(content, encoding="utf-8", newline="\n")
    print(f"✅ Wrote {MANIFEST.relative_to(PROJECT_DIR)} ({len(content)} bytes)")
    return 0


def cmd_stdout(content: str) -> int:
    sys.stdout.write(content)
    return 0


def cmd_check(content: str) -> int:
    current = MANIFEST.read_text(encoding="utf-8")
    if current == content:
        return 0
    diff = difflib.unified_diff(
        current.splitlines(keepends=True),
        content.splitlines(keepends=True),
        fromfile=f"{MANIFEST.relative_to(PROJECT_DIR)} (current)",
        tofile=f"{MANIFEST.relative_to(PROJECT_DIR)} (expected)",
        n=2,
    )
    sys.stderr.write("❌ plugin.json is out of sync with .claude/ contents.\n")
    sys.stderr.write("   Run: python scripts/regenerate_plugin_manifest.py\n\n")
    sys.stderr.writelines(diff)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="write plugin.json (default)")
    group.add_argument("--stdout", action="store_true", help="print to stdout")
    group.add_argument("--check", action="store_true", help="exit 1 if plugin.json is stale")
    args = parser.parse_args()

    content = build_manifest()
    if args.stdout:
        return cmd_stdout(content)
    if args.check:
        return cmd_check(content)
    return cmd_write(content)


if __name__ == "__main__":
    sys.exit(main())
