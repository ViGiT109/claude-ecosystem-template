#!/usr/bin/env python3
"""SessionStart hook: injects current project focus into Claude's context.

Outputs:
- 🔴 BOOTSTRAP REQUIRED block when the template hasn't been initialised
  (placeholder `${PROJECT_NAME}` still present in README.md / CLAUDE.md / .ecosystem.toml)
- First lines of `.memory/activeContext.md` (current phase, sprint focus)
- Freshness of `.memory/lessons.md` (last-updated date)
- Audit-freshness reminder when no `event: audit_complete` entry in
  `.memory/audit_history.jsonl` exists in the last 14 days
- Uncommitted git changes status

The stdout of this script is automatically injected into the Claude Code session context.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
PLACEHOLDER = "${PROJECT_NAME}"
BOOTSTRAP_SCAN_FILES = ("README.md", "CLAUDE.md", ".ecosystem.toml")

# Context window budgets per model (tokens). Used by emit_context_window_status().
MODEL_WINDOWS = {
    "opus": 1_000_000,
    "sonnet": 200_000,
    "haiku": 200_000,
}
DEFAULT_MODEL = "opus"
# Rough heuristic: average ~4 bytes per token in JSONL transcripts.
BYTES_PER_TOKEN = 4


def check_bootstrap_done() -> bool:
    """Return True if the user needs to run bootstrap (placeholders unresolved).

    Skipped when `TEMPLATE_README.md` is present — that means we are *inside*
    the template repo itself, not a downstream clone. `bootstrap.ps1` deletes
    TEMPLATE_README.md as part of its first-run sequence.
    """
    if (PROJECT_DIR / "TEMPLATE_README.md").exists():
        return False

    flagged: list[str] = []
    for name in BOOTSTRAP_SCAN_FILES:
        path = PROJECT_DIR / name
        if not path.exists():
            continue
        try:
            if PLACEHOLDER in path.read_text(encoding="utf-8"):
                flagged.append(name)
        except OSError:
            continue
    if not flagged:
        return False

    print("# 🔴 BOOTSTRAP REQUIRED")
    print()
    print(f"Найдены нерезолвленные плейсхолдеры `{PLACEHOLDER}` в файлах:")
    for name in flagged:
        print(f"  - {name}")
    print()
    print("**Перед продолжением запусти `.\\bootstrap.ps1` (Windows) или `./bootstrap.sh`.**")
    print()
    print("Пока bootstrap не выполнен — проект не инициализирован: пути, имена и")
    print("языковая обвязка всё ещё в шаблонной форме.")
    return True


def emit_active_context() -> None:
    path = PROJECT_DIR / ".memory" / "activeContext.md"
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    # First 25 lines typically contain YAML frontmatter + current phase
    head = "\n".join(lines[:25]).rstrip()
    if head:
        print("## 📍 activeContext.md (фокус спринта)")
        print(head)
        print()


def emit_lessons_freshness() -> None:
    path = PROJECT_DIR / ".memory" / "lessons.md"
    if not path.exists():
        return
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime)
    age_days = (dt.datetime.now() - mtime).days
    if age_days < 7:
        status = "🟢 свежий"
    elif age_days < 30:
        status = "🟡 начинает устаревать"
    else:
        status = "🔴 пора обновить"
    print(f"## 📚 lessons.md: {status} (обновлён {age_days} дн. назад — {mtime:%Y-%m-%d})")
    print()


def emit_audit_freshness() -> None:
    """Emit a 🟡 reminder when no full ecosystem audit has run in >14 days.

    The check looks at `.memory/audit_history.jsonl` and considers ONLY entries
    where `event == "audit_complete"` — those are appended by `/audit_ecosystem`
    after Phase E. Routine `stop_hook` entries (one per Claude turn) are ignored
    because they would otherwise mask the actual audit cadence.
    """
    path = PROJECT_DIR / ".memory" / "audit_history.jsonl"
    threshold_days = 14

    if not path.exists():
        print("## 📊 audit: 🟡 audit_history.jsonl отсутствует — запусти `/audit_ecosystem`, чтобы начать отслеживание")
        print()
        return

    last_complete: dt.datetime | None = None
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if entry.get("event") != "audit_complete":
                continue
            stamp = entry.get("timestamp") or entry.get("date")
            if not stamp:
                continue
            try:
                ts = dt.datetime.fromisoformat(stamp.rstrip("Z"))
            except ValueError:
                continue
            if last_complete is None or ts > last_complete:
                last_complete = ts
    except OSError:
        return

    if last_complete is None:
        print("## 📊 audit: 🟡 не зафиксировано ни одного запуска `/audit_ecosystem` — стоит запустить")
        print()
        return

    age_days = (dt.datetime.utcnow() - last_complete).days
    if age_days > threshold_days:
        print(f"## 📊 audit: 🟡 последний полный аудит был {age_days} дн. назад — запусти `/audit_ecosystem`")
        print()
    # Fresh → silent (avoid noise on every session start).


def _read_stdin_json() -> dict:
    """Read a JSON object from stdin without blocking on an empty pipe.

    Returns `{}` on empty stdin, JSON decode errors, or any I/O error. Hooks
    invoked outside Claude Code (e.g. smoke tests) have no stdin attached;
    `sys.stdin.read()` returns "" in that case and we degrade gracefully.
    """
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


def _resolve_model() -> str:
    """Pick a model key from `MODEL_WINDOWS` using the `CLAUDE_MODEL` env var.

    Accepts loose values like `opus`, `claude-opus-4-7`, `sonnet`, `haiku`.
    Falls back to `DEFAULT_MODEL` when unset or unrecognised.
    """
    raw = (os.environ.get("CLAUDE_MODEL") or "").lower()
    for key in MODEL_WINDOWS:
        if key in raw:
            return key
    return DEFAULT_MODEL


def _estimate_session_tokens(payload: dict) -> int | None:
    """Estimate tokens consumed in the live session via transcript size.

    Claude Code passes `transcript_path` in the SessionStart stdin payload.
    Tokens are approximated as `file_bytes // BYTES_PER_TOKEN` — coarse but
    monotonic, which is all the 70%/90% gate needs. Returns `None` when no
    usable transcript path is available.
    """
    transcript = payload.get("transcript_path")
    if not transcript or not isinstance(transcript, str):
        return None
    path = Path(transcript)
    if not path.exists() or not path.is_file():
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    return max(0, size // BYTES_PER_TOKEN)


def emit_context_window_status(payload: dict) -> None:
    """Emit a 🔄 SESSION HANDOFF block when the session is past 70% of the window.

    Non-blocking — purely advisory. Silent when usage is unknown or below the
    threshold to keep new sessions clean. See `.agents/rules/model-policy.md`
    §Context Window Awareness for the policy this enforces.
    """
    tokens = _estimate_session_tokens(payload)
    if tokens is None:
        return
    model = _resolve_model()
    window = MODEL_WINDOWS[model]
    pct = (tokens / window) * 100 if window else 0
    if pct < 70:
        return

    if pct >= 90:
        print("## ❌ SESSION HANDOFF — CRITICAL")
    else:
        print("## 🔄 SESSION HANDOFF RECOMMENDED")
    print()
    print(f"- Оценка контекста: **{tokens:,} токенов** (~{pct:.0f}% от окна {model} {window:,})")
    print("- Переключение модели внутри сессии **не** освобождает контекст — это делает только новая сессия.")
    print("- Рекомендация: запусти `/handoff` → стартуй новую сессию → `/new_session`.")
    print()


def emit_git_status() -> None:
    try:
        out = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            cwd=str(PROJECT_DIR),
        )
    except (OSError, subprocess.TimeoutExpired):
        return
    lines = [ln for ln in (out.stdout or "").splitlines() if ln.strip()]
    if not lines:
        print("## 🧹 git: чисто (нет незакоммиченных изменений)")
    else:
        print(f"## ⚠️ git: {len(lines)} незакоммиченных изменени(е/я)")
        for ln in lines[:10]:
            print(f"  {ln}")
        if len(lines) > 10:
            print(f"  ... и ещё {len(lines) - 10}")
    print()


def main() -> int:
    # Bootstrap guard runs first and short-circuits the normal session preamble.
    if check_bootstrap_done():
        return 0

    payload = _read_stdin_json()

    print("# 🚀 Контекст проекта (авто-инжект из SessionStart-хука)")
    print()
    emit_context_window_status(payload)
    emit_active_context()
    emit_lessons_freshness()
    emit_audit_freshness()
    emit_git_status()
    print("_Запусти `/new_session`, чтобы загрузить полный контекст._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
