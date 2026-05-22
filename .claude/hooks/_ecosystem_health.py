"""Shared helpers for ecosystem self-diagnostics.

Used by SessionStart and Stop hooks (and the diagnostic dashboard) to read
append-only journal files under `.memory/` and compute freshness signals.

**Constraint:** stdlib only. These helpers run inside hooks that may execute
outside `.venv` (especially on freshly-cloned downstream projects), so no
third-party imports — `json`, `pathlib`, `datetime`, `os`, `re` only.

Public surface:
    - `audit_age_days()`           — days since the last `audit_complete` event.
    - `last_audit_info()`          — dict with the last full-audit metadata.
    - `stop_hook_count_since_audit()` — count of stop_hook rows since the
                                     last `audit_complete`.
    - `consolidate_age_days()`     — days since the last `consolidate_complete`.
    - `hook_health_age_hours()`    — hours since the last `hook_health_check`.
    - `audit_status()`             — combined verdict for audit freshness:
                                     ("ok"|"aging"|"required", reason: str).
    - `consolidate_status()`       — same shape for consolidate.
    - `hook_health_status()`       — same shape for hook health.

All "age" helpers return a sentinel of 999 days / 999 hours when the file
or the relevant event row is missing — callers may treat this as "very
stale" and trigger the strongest signal.

Thresholds live in this module so a single edit retunes both the inject
markers (session_start.py) and the dashboard (diag_dashboard.py).
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
AUDIT_LOG = PROJECT_DIR / ".memory" / "audit_history.jsonl"
LESSONS_FILE = PROJECT_DIR / ".memory" / "lessons.md"

# Thresholds — tune here, propagates to session_start.py and diag_dashboard.py.
AUDIT_REQUIRED_DAYS = 7
AUDIT_AGING_DAYS = 3
AUDIT_REQUIRED_STOP_HOOKS = 20

CONSOLIDATE_RECOMMENDED_DAYS = 30
CONSOLIDATE_LESSON_COUNT = 20

HOOK_HEALTH_STALE_HOURS = 24
HOOK_HEALTH_CRITICAL_HOURS = 48


# ---------------------------------------------------------------------------
# Low-level journal iteration

def _iter_entries() -> list[dict]:
    """Yield every parseable JSONL entry in `audit_history.jsonl`."""
    if not AUDIT_LOG.exists():
        return []
    out: list[dict] = []
    try:
        for raw in AUDIT_LOG.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                out.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return out


def _parse_ts(value) -> dt.datetime | None:
    """Parse 'YYYY-MM-DDTHH:MM:SSZ' or ISO with offset; tolerate junk."""
    if not isinstance(value, str):
        return None
    try:
        # Drop trailing Z (treat as UTC) and any +00:00 offset uniformly.
        s = value.rstrip("Z")
        return dt.datetime.fromisoformat(s).replace(tzinfo=None)
    except ValueError:
        return None


def _now_naive_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(tzinfo=None)


def _latest_of_event(event_name: str) -> dict | None:
    """Return the most recent entry whose `event` field matches."""
    latest: dict | None = None
    latest_ts: dt.datetime | None = None
    for e in _iter_entries():
        if e.get("event") != event_name:
            continue
        ts = _parse_ts(e.get("timestamp") or e.get("date"))
        if ts is None:
            continue
        if latest_ts is None or ts > latest_ts:
            latest_ts = ts
            latest = e
    return latest


# ---------------------------------------------------------------------------
# Public: age helpers

def audit_age_days() -> int:
    """Days since the last `audit_complete` row; 999 if never seen.

    Filtered by `event == "audit_complete"` because `audit_history.jsonl` is
    also appended to by `stop_audit.py` on every Claude turn — without the
    filter the "last entry" is always seconds old.
    """
    last = _latest_of_event("audit_complete")
    if last is None:
        return 999
    ts = _parse_ts(last.get("timestamp") or last.get("date"))
    if ts is None:
        return 999
    return (_now_naive_utc() - ts).days


def last_audit_info() -> dict | None:
    """The most recent `audit_complete` entry, or None."""
    return _latest_of_event("audit_complete")


def stop_hook_count_since_audit() -> int:
    """Count `stop_hook` rows newer than the latest `audit_complete`.

    Returns -1 when `audit_history.jsonl` is missing.
    Returns the full count when no `audit_complete` has ever been recorded.
    """
    if not AUDIT_LOG.exists():
        return -1
    last_audit = _latest_of_event("audit_complete")
    cutoff = _parse_ts((last_audit or {}).get("timestamp") or (last_audit or {}).get("date"))
    count = 0
    for e in _iter_entries():
        if e.get("event") != "stop_hook":
            continue
        ts = _parse_ts(e.get("timestamp") or e.get("date"))
        if ts is None:
            continue
        if cutoff is None or ts > cutoff:
            count += 1
    return count


def consolidate_age_days() -> int:
    """Days since last `consolidate_complete`; 999 if never seen."""
    last = _latest_of_event("consolidate_complete")
    if last is None:
        return 999
    ts = _parse_ts(last.get("timestamp"))
    if ts is None:
        return 999
    return (_now_naive_utc() - ts).days


def hook_health_age_hours() -> int:
    """Hours since last `hook_health_check`; 9999 if never seen."""
    last = _latest_of_event("hook_health_check")
    if last is None:
        return 9999
    ts = _parse_ts(last.get("timestamp"))
    if ts is None:
        return 9999
    return int((_now_naive_utc() - ts).total_seconds() // 3600)


def lessons_count() -> int:
    """Count `### Memory Item:` headers in `.memory/lessons.md`; 0 on absence."""
    if not LESSONS_FILE.exists():
        return 0
    try:
        text = LESSONS_FILE.read_text(encoding="utf-8")
    except OSError:
        return 0
    return text.count("### Memory Item:")


# ---------------------------------------------------------------------------
# Public: combined verdicts

def audit_status() -> tuple[str, str]:
    """Return ("ok"|"aging"|"required", explanation)."""
    age = audit_age_days()
    stop_count = stop_hook_count_since_audit()
    if age >= AUDIT_REQUIRED_DAYS or stop_count >= AUDIT_REQUIRED_STOP_HOOKS:
        if age == 999:
            return "required", "no `/audit_ecosystem` runs recorded yet"
        return "required", (
            f"last audit {age} day(s) ago, "
            f"{stop_count} session(s) since"
        )
    if age >= AUDIT_AGING_DAYS:
        return "aging", f"last audit {age} day(s) ago"
    return "ok", f"last audit {age} day(s) ago"


def consolidate_status() -> tuple[str, str]:
    """Return ("ok"|"recommended", explanation)."""
    age = consolidate_age_days()
    lc = lessons_count()
    if age == 999 and lc < CONSOLIDATE_LESSON_COUNT:
        # No consolidate history yet, and not many lessons — silent.
        return "ok", f"{lc} lesson(s), never consolidated"
    if age >= CONSOLIDATE_RECOMMENDED_DAYS or lc >= CONSOLIDATE_LESSON_COUNT:
        if age == 999:
            return "recommended", f"{lc} lesson(s), never consolidated"
        return "recommended", f"last consolidate {age} day(s) ago, {lc} lesson(s)"
    return "ok", f"last consolidate {age} day(s) ago, {lc} lesson(s)"


def hook_health_status() -> tuple[str, str]:
    """Return ("ok"|"stale"|"critical", explanation)."""
    hrs = hook_health_age_hours()
    if hrs >= HOOK_HEALTH_CRITICAL_HOURS:
        if hrs == 9999:
            return "critical", "no `hook_health_check` events recorded"
        return "critical", f"last hook check {hrs}h ago"
    if hrs >= HOOK_HEALTH_STALE_HOURS:
        return "stale", f"last hook check {hrs}h ago"
    return "ok", f"last hook check {hrs}h ago"
