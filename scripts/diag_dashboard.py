#!/usr/bin/env python3
"""Ecosystem diagnostic dashboard.

Reads every append-only journal in `.memory/` plus a few static config
files, then prints a markdown sweep of ecosystem health: audits,
lessons, retrieval mix, session trajectories, hooks, version sync.

Two modes:
    python scripts/diag_dashboard.py            # full report (~60 lines)
    python scripts/diag_dashboard.py --summary  # 5 traffic-light lines

The script is the user-facing observability layer (Layer C of v2.2).
Slash-command `/diag_status` invokes the summary mode.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Common helpers shared with hooks live in .claude/hooks/_ecosystem_health.py.
PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
sys.path.insert(0, str(PROJECT_DIR / ".claude" / "hooks"))
import _ecosystem_health as _eh  # noqa: E402

AUDIT_LOG = PROJECT_DIR / ".memory" / "audit_history.jsonl"
TRAJECTORIES = PROJECT_DIR / ".memory" / "session_trajectories.jsonl"
RETRIEVAL_LOGS = PROJECT_DIR / ".memory" / "retrieval_logs.jsonl"
LESSONS = PROJECT_DIR / ".memory" / "lessons.md"


# ---------------------------------------------------------------------------
# Generic JSONL reader

def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                rows.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
    except OSError:
        return []
    return rows


# ---------------------------------------------------------------------------
# Sections

def section_audits() -> list[str]:
    rows = [r for r in _read_jsonl(AUDIT_LOG) if r.get("event") == "audit_complete"]
    rows.sort(key=lambda r: r.get("timestamp") or r.get("date") or "")
    lines = ["## Audits"]
    if not rows:
        lines.append("- No `audit_complete` events recorded yet.")
        return lines
    last = rows[-1]
    age = _eh.audit_age_days()
    lines.append(
        f"- Last: {last.get('tag_under_audit', '?')} "
        f"{last.get('rating', '')} {last.get('score', '?')} "
        f"({age} day(s) ago)"
    )
    if len(rows) > 1:
        trend = " → ".join(str(r.get("score", "?")) for r in rows[-5:])
        lines.append(f"- Trend (last {min(5, len(rows))}): {trend}")
    stop_since = _eh.stop_hook_count_since_audit()
    lines.append(f"- Sessions since last audit: {stop_since}")
    return lines


def section_lessons() -> list[str]:
    count = _eh.lessons_count()
    age_days = _lessons_file_age_days()
    status, reason = _eh.consolidate_status()
    icon = {"ok": "🟢", "recommended": "🟡"}.get(status, "❓")
    promo_status, promo_reason = _eh.promotion_status()
    promo_icon = {"ok": "🟢", "recommended": "🟡"}.get(promo_status, "❓")
    lines = ["## Lessons"]
    lines.append(f"- Count: {count} (file age: {age_days} day(s))")
    lines.append(f"- Consolidate: {icon} {reason}")
    lines.append(f"- Promotion:   {promo_icon} {promo_reason}")
    if promo_status == "recommended":
        for title in _eh.pending_promotions():
            lines.append(f"  • {title}")
    return lines


def _lessons_file_age_days() -> int:
    if not LESSONS.exists():
        return 999
    age_s = dt.datetime.now().timestamp() - LESSONS.stat().st_mtime
    return int(age_s // 86400)


def section_retrieval() -> list[str]:
    rows = _read_jsonl(RETRIEVAL_LOGS)
    lines = ["## Retrieval mix (all-time)"]
    if not rows:
        lines.append("- No retrieval logs.")
        return lines
    modes = Counter(r.get("mode", "?") for r in rows)
    total = sum(modes.values())
    if total:
        parts = [f"{m}: {n / total:.0%}" for m, n in modes.most_common()]
        lines.append(f"- Total queries: {total}; " + ", ".join(parts))
    collections = Counter(r.get("collection", "?") for r in rows)
    lines.append("- Collections: " + ", ".join(f"{c}: {n}" for c, n in collections.most_common()))
    return lines


def section_trajectories() -> list[str]:
    rows = _read_jsonl(TRAJECTORIES)
    lines = ["## Trajectories"]
    if not rows:
        lines.append("- No `session_trajectories.jsonl` rows yet.")
        return lines
    outcomes = Counter(r.get("outcome", "unknown") for r in rows)
    durations = [r.get("duration_min") for r in rows if isinstance(r.get("duration_min"), (int, float))]
    avg = sum(durations) / len(durations) if durations else None
    lines.append(f"- Sessions logged: {len(rows)}")
    lines.append("- Outcomes: " + ", ".join(f"{k}: {v}" for k, v in outcomes.most_common()))
    if avg is not None:
        lines.append(f"- Avg duration: {avg:.0f} min (n={len(durations)})")
    return lines


def section_hooks() -> list[str]:
    status, reason = _eh.hook_health_status()
    icon = {"ok": "🟢", "stale": "🟡", "critical": "🔴"}.get(status, "❓")
    lines = ["## Hooks"]
    lines.append(f"- Health: {icon} {reason}")

    last = next(
        (r for r in reversed(_read_jsonl(AUDIT_LOG)) if r.get("event") == "hook_health_check"),
        None,
    )
    if last:
        failed = last.get("failed_hooks") or []
        lines.append(f"- Last check: {last.get('status', '?')} ({last.get('checked', '?')} hooks probed)")
        if failed:
            for f in failed:
                lines.append(f"  • {f.get('event', '?')} → {f.get('script', '?')}: {f.get('status', '?')}")
    return lines


def section_version_sync() -> list[str]:
    lines = ["## Version sync"]
    plugin_json = PROJECT_DIR / ".claude-plugin" / "plugin.json"
    changelog = PROJECT_DIR / "CHANGELOG.md"
    eco_toml = PROJECT_DIR / ".ecosystem.toml"
    pv = cv = ev = "?"
    if plugin_json.exists():
        try:
            pv = json.loads(plugin_json.read_text(encoding="utf-8")).get("version", "?")
        except Exception:
            pv = "(parse error)"
    if changelog.exists():
        for line in changelog.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^##\s+\[(\d+\.\d+\.\d+)\]", line)
            if m:
                cv = m.group(1)
                break
    if eco_toml.exists():
        try:
            import tomllib
            with eco_toml.open("rb") as f:
                data = tomllib.load(f)
            ev = (data.get("ecosystem") or {}).get("version") or "(no version)"
        except Exception:
            ev = "(parse error)"
    lines.append(f"- plugin.json:     {pv}")
    lines.append(f"- CHANGELOG.md:    {cv}")
    lines.append(f"- .ecosystem.toml: {ev}")
    in_sync = pv == cv and (ev in (pv, "(no version)"))
    lines.append(f"- Status: {'🟢 synced' if in_sync else '🔴 drift'}")
    last_tag = _last_git_tag()
    if last_tag:
        lines.append(f"- Last tag: {last_tag}")
    return lines


def _last_git_tag() -> str | None:
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=str(PROJECT_DIR), timeout=5, check=False,
        )
        return r.stdout.strip() or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Summary mode

def render_summary() -> list[str]:
    audit_status, _ = _eh.audit_status()
    cons_status, _ = _eh.consolidate_status()
    hook_status, _ = _eh.hook_health_status()
    icon = {"ok": "🟢", "aging": "🟡", "required": "🔴",
            "recommended": "🟡", "stale": "🟡", "critical": "🔴"}

    # Quick version-sync check
    plugin_json = PROJECT_DIR / ".claude-plugin" / "plugin.json"
    changelog = PROJECT_DIR / "CHANGELOG.md"
    pv = cv = None
    if plugin_json.exists():
        try:
            pv = json.loads(plugin_json.read_text(encoding="utf-8")).get("version")
        except Exception:
            pass
    if changelog.exists():
        for line in changelog.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^##\s+\[(\d+\.\d+\.\d+)\]", line)
            if m:
                cv = m.group(1)
                break
    ver_ok = pv and cv and pv == cv

    promo_status, _ = _eh.promotion_status()

    rows = [
        f"audit:     {icon.get(audit_status, '❓')} {audit_status}",
        f"lessons:   {icon.get(cons_status, '❓')} {cons_status}",
        f"promotion: {icon.get(promo_status, '❓')} {promo_status}",
        f"hooks:     {icon.get(hook_status, '❓')} {hook_status}",
        f"version:   {'🟢 synced' if ver_ok else '🔴 drift'} (plugin.json={pv}, CHANGELOG={cv})",
    ]
    return ["📊 Ecosystem health summary"] + rows


# ---------------------------------------------------------------------------
# Main

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ecosystem diagnostic dashboard.")
    p.add_argument("--summary", action="store_true",
                   help="Print 4-line traffic-light summary instead of full report.")
    args = p.parse_args(argv)

    if args.summary:
        for line in render_summary():
            print(line)
        return 0

    print(f"# Ecosystem Health — {dt.date.today().isoformat()}")
    print()
    for section_fn in (
        section_audits, section_lessons, section_retrieval,
        section_trajectories, section_hooks, section_version_sync,
    ):
        for line in section_fn():
            print(line)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
