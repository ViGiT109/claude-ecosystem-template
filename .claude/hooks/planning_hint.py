#!/usr/bin/env python3
"""UserPromptSubmit hook: emit a unified 🧭 PLAN + 💡 MODEL block on triggers.

Reads a JSON payload from stdin (`{"prompt": "..."}`) and prints the combined
recommendation block when the user's prompt looks like planning / architectural
work. Triggers cover RU and EN keyword sets plus a heuristic for prompts that
mention three or more files. Always exits 0 — this hook is advisory.

Behavior is governed by `.agents/rules/model-policy.md` §Planning hint and the
AGENTS.md «Planning-phase signaling» section.

Killswitch: set `CLAUDE_DISABLE_PLANNING_HINT=1` to silence the hook entirely.
"""
from __future__ import annotations

import json
import os
import re
import sys

MIN_PROMPT_LEN = 20

RU_TRIGGER = re.compile(
    r"(?ix)"
    r"(?:"
    r"спроектируй|спроектируем|разработай|архитектур|"
    r"реализуй\s+\S*\s*(?:фич|функционал|модул)|"
    r"рефактор|мигра|перепиши|редизайн"
    r")",
)

EN_TRIGGER = re.compile(
    r"(?ix)"
    r"\b(?:"
    r"design|architect|implement|refactor|migration|rewrite|redesign|"
    r"spec|specification|plan|planning"
    r")\b",
)

FILE_REF = re.compile(
    r"(?i)[\w./-]+\.(?:py|md|json|toml|yaml|yml|ps1|ts|tsx|js|jsx|go|rs|java|kt|sh|sql)\b",
)
FILE_REF_THRESHOLD = 3


def _read_stdin_json() -> dict:
    """Read JSON payload from stdin; return `{}` on empty/invalid input."""
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _find_trigger(prompt: str) -> str | None:
    """Return a human-readable trigger label, or None if no trigger matched."""
    m = RU_TRIGGER.search(prompt)
    if m:
        return m.group(0).lower()
    m = EN_TRIGGER.search(prompt)
    if m:
        return m.group(0).lower()
    file_refs = {m.group(0) for m in FILE_REF.finditer(prompt)}
    if len(file_refs) >= FILE_REF_THRESHOLD:
        return f"multiple file references ({len(file_refs)})"
    return None


def _emit_block(trigger: str) -> None:
    print("🧭 PLAN PHASE RECOMMENDED")
    print(f"   Trigger: «{trigger}»")
    print("   Suggested action: Enter Plan Mode (Shift+Tab)")
    print("💡 MODEL: Opus 4.7")
    print("   Reason: planning + architectural reasoning (see .agents/rules/model-policy.md)")


def main() -> int:
    # Dry-run mode — used by `scripts/check_hook_health.py`.
    if os.environ.get("HOOK_DRYRUN") == "1":
        return 0

    if os.environ.get("CLAUDE_DISABLE_PLANNING_HINT") == "1":
        return 0

    payload = _read_stdin_json()
    prompt = payload.get("prompt")
    if not isinstance(prompt, str):
        return 0

    stripped = prompt.strip()
    if len(stripped) < MIN_PROMPT_LEN:
        return 0

    trigger = _find_trigger(stripped)
    if trigger is None:
        return 0

    _emit_block(trigger)
    return 0


if __name__ == "__main__":
    sys.exit(main())
