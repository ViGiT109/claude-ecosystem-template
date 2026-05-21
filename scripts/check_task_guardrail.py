#!/usr/bin/env python3
"""Pre-commit hook: blocks commit when task.md has unchecked [ ] or in-progress [/] items."""
import os
import re
import sys


def main() -> int:
    task_files: list[str] = []

    if os.path.exists("task.md"):
        task_files.append("task.md")

    found: list[tuple[str, int, str]] = []
    for f in task_files:
        try:
            with open(f, encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if re.match(r"\s*-\s*\[[ /]\]", line):
                        found.append((f, i, line.strip()))
        except OSError:
            pass

    if found:
        print("❌ НАЙДЕНЫ БРОШЕННЫЕ ЗАДАЧИ — коммит заблокирован!")
        for f, n, line in found:
            print(f"  {f}:{n}: {line}")
        print("\nЗакрой все [ ] и [/] пункты в task.md перед коммитом.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
