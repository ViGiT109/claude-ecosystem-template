#!/usr/bin/env python3
"""statusLine hook for Claude Code.

Renders a single line of text that Claude Code displays in its status area.
Invoked by the harness with a JSON payload on stdin (best-effort — schema is
not contractual, so we treat all fields as optional).

Output (single line, no trailing newline):
    🤖 <model> | 🌿 <branch> | 📊 <ctx%>

Segments are silently dropped when their source data is unavailable so the line
never errors out.

Context-usage estimate uses the same heuristic as `session_start.py`
(transcript bytes ÷ 4 ≈ tokens) against `MODEL_WINDOWS`. It is a rough proxy,
not a precise account.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Keep in sync with session_start.py.
MODEL_WINDOWS = {
    "opus": 1_000_000,
    "sonnet": 200_000,
    "haiku": 200_000,
}
DEFAULT_MODEL = "opus"
BYTES_PER_TOKEN = 4


def _read_stdin_json() -> dict:
    """Read the JSON payload Claude Code passes on stdin. Return {} on any error."""
    if sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _resolve_model(payload: dict) -> str:
    """Resolve the model name from payload → env → default."""
    raw = (
        payload.get("model")
        or (payload.get("session") or {}).get("model")
        or os.environ.get("CLAUDE_MODEL")
        or DEFAULT_MODEL
    )
    name = str(raw).lower()
    for key in MODEL_WINDOWS:
        if key in name:
            return key
    return DEFAULT_MODEL


def _git_branch() -> str | None:
    """Return the current git branch, or None if not in a git repo."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    branch = out.stdout.strip()
    return branch or None


def _transcript_size_bytes(payload: dict) -> int | None:
    """Locate the active transcript JSONL and return its size in bytes."""
    candidate = payload.get("transcript_path") or (payload.get("session") or {}).get(
        "transcript_path"
    )
    if candidate:
        path = Path(str(candidate))
        if path.is_file():
            try:
                return path.stat().st_size
            except OSError:
                return None
    return None


def _context_percent(payload: dict, model: str) -> int | None:
    """Estimate current context usage as a percentage of the active model's window."""
    size = _transcript_size_bytes(payload)
    if size is None:
        return None
    tokens = size // BYTES_PER_TOKEN
    window = MODEL_WINDOWS.get(model, MODEL_WINDOWS[DEFAULT_MODEL])
    pct = int(round(100 * tokens / window))
    return max(0, min(pct, 999))


def _format_branch(branch: str, *, max_len: int = 40) -> str:
    """Truncate long branch names so the status line stays compact."""
    if len(branch) <= max_len:
        return branch
    return branch[: max_len - 1] + "…"


def build_status_line(payload: dict) -> str:
    model = _resolve_model(payload)
    segments = [f"🤖 {model}"]

    branch = _git_branch()
    if branch:
        segments.append(f"🌿 {_format_branch(branch)}")

    pct = _context_percent(payload, model)
    if pct is not None:
        marker = "📊"
        if pct >= 90:
            marker = "🔴"
        elif pct >= 70:
            marker = "🟡"
        segments.append(f"{marker} {pct}% ctx")

    return " | ".join(segments)


def main() -> None:
    payload = _read_stdin_json()
    line = build_status_line(payload)
    # Single line, no trailing newline — Claude Code adds its own framing.
    sys.stdout.write(line)


if __name__ == "__main__":
    main()
