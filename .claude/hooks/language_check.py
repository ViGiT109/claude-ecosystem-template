#!/usr/bin/env python3
"""UserPromptSubmit hook: enforces reply-language alignment with prompt language.

Reads JSON from stdin (`{"prompt": "..."}`). If the user's prompt contains
Cyrillic characters above a small threshold (to ignore incidental code-mention),
prints a one-line reminder for the agent to reply in Russian. The reminder is
injected into Claude Code's context like any other UserPromptSubmit hook output.

This is the deterministic counterpart to the soft auto-memory note
"feedback-language-russian" — that note can be ignored under context drift;
this hook fires on every user turn and cannot be silently skipped.

Killswitch: set `CLAUDE_DISABLE_LANGUAGE_CHECK=1` to silence the hook entirely.
Always exits 0 — advisory only.

References:
  - .agents/rules/common.md §Reply language (if added there)
  - .memory/lessons.md → "Mirror prompt language, not codebase language"
"""
from __future__ import annotations

import json
import os
import re
import sys

# Russian/Ukrainian/Belarusian/etc. block. Narrow enough to avoid false positives
# from incidental Cyrillic in code identifiers or pasted error messages.
CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")
# Threshold: at least this many Cyrillic characters → treat as Russian-language prompt.
# 8 covers any reasonable Russian phrase ("привет" + a couple of words) while
# ignoring single-token mentions like "переменная `аргумент`" in an otherwise
# English prompt.
CYRILLIC_MIN = 8


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


def main() -> int:
    if os.environ.get("CLAUDE_DISABLE_LANGUAGE_CHECK") == "1":
        return 0

    payload = _read_stdin_json()
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        return 0

    cyrillic_count = len(CYRILLIC_RE.findall(prompt))
    if cyrillic_count < CYRILLIC_MIN:
        return 0

    print("🗣️ LANGUAGE: промпт на русском — отвечай по-русски.")
    print(
        "   User-facing текст (сообщения, end-of-turn summaries) — на русском; "
        "идентификаторы кода, Conventional Commits и артефакты шаблона — на английском."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
