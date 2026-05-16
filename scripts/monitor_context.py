#!/usr/bin/env python3
"""Estimate the size of files loaded into the AI assistant's context window."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONTEXT_DIRS = [
    PROJECT_ROOT / ".agents",
    PROJECT_ROOT / ".memory",
]

CONTEXT_FILES = [
    PROJECT_ROOT / "CLAUDE.md",
    PROJECT_ROOT / "task.md",
]


def main() -> None:
    print("=== Context file size estimate ===")
    total_bytes = 0
    entries: list[tuple[str, int]] = []

    for d in CONTEXT_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("*.md"):
            size = f.stat().st_size
            entries.append((str(f.relative_to(PROJECT_ROOT)), size))
            total_bytes += size

    for f in CONTEXT_FILES:
        if f.exists():
            size = f.stat().st_size
            entries.append((str(f.relative_to(PROJECT_ROOT)), size))
            total_bytes += size

    entries.sort(key=lambda x: x[1], reverse=True)

    for name, size in entries:
        print(f"  {size:>8,} B  {name}")

    print("-----------------------------------")
    print(f"Total static context size: ~{total_bytes // 1024} KB")
    print(f"Estimated tokens (1 token ~ 4 chars): ~{total_bytes // 4:,} tokens")


if __name__ == "__main__":
    main()
