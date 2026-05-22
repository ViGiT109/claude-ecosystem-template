#!/usr/bin/env python3
"""Hook health-check.

Verifies that every hook declared in `.claude/settings.json::hooks` is
intact: the target script file exists and runs to completion without
crashing when invoked with `HOOK_DRYRUN=1` and a synthetic empty-JSON
stdin payload. This catches the most common failure modes — import
errors after a Python upgrade, syntax errors after an edit, missing
file references, dependency rot.

The dry-run flag is honoured by each hook: they short-circuit before
producing side effects (stdout inject, audit log writes, exit code 2
blocks) and return 0.

Result is appended as a `hook_health_check` event to
`.memory/audit_history.jsonl` so `session_start.py` can surface "hook
health stale" markers via the session-triggered-cron mechanism.

Usage
-----
    python scripts/check_hook_health.py            # check all hooks
    python scripts/check_hook_health.py --verbose  # print every probe

Exit codes
----------
    0 — all hooks healthy
    1 — one or more hooks failed (details in stderr + audit_history)
    2 — `.claude/settings.json` missing or unparseable
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")).resolve()
SETTINGS = PROJECT_DIR / ".claude" / "settings.json"
AUDIT_LOG = PROJECT_DIR / ".memory" / "audit_history.jsonl"

HOOK_TIMEOUT_S = 10


def discover_hooks() -> list[dict]:
    """Walk `.claude/settings.json::hooks` and yield one record per hook.

    Schema (Claude Code settings):
        {
          "hooks": {
            "<EventName>": [
              {
                "matcher": "...",          # optional, only on PreToolUse
                "hooks": [
                  {"type": "command", "command": "python .../_run.py .../X.py"}
                ]
              }
            ]
          }
        }
    """
    if not SETTINGS.is_file():
        raise FileNotFoundError(f"{SETTINGS} not found")
    data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    hooks_cfg = data.get("hooks") or {}
    results: list[dict] = []
    for event_name, event_entries in hooks_cfg.items():
        if not isinstance(event_entries, list):
            continue
        for entry in event_entries:
            matcher = entry.get("matcher")
            for h in entry.get("hooks") or []:
                cmd = h.get("command") or ""
                results.append({
                    "event": event_name,
                    "matcher": matcher,
                    "command": cmd,
                    "timeout": h.get("timeout"),
                    "script": _extract_script(cmd),
                })
    return results


def _extract_script(command: str) -> str | None:
    """Return the target script path from a `_run.py`-style command, else None."""
    tokens = command.split()
    # Prefer the last `.py` token that is not `_run.py` itself.
    pys = [t for t in tokens if t.endswith(".py")]
    if not pys:
        return None
    # If launcher pattern: `python _run.py target.py [args]`, target is after _run.py.
    for i, tok in enumerate(tokens):
        if tok.endswith("_run.py") and i + 1 < len(tokens):
            return tokens[i + 1]
    # Otherwise just take the last .py token.
    return pys[-1]


def probe_hook(record: dict) -> dict:
    """Run one hook with HOOK_DRYRUN=1 + empty-JSON stdin; capture outcome."""
    script = record["script"]
    out: dict = {**record, "status": None, "detail": ""}

    if script is None:
        out["status"] = "skipped"
        out["detail"] = "no script path resolved from command"
        return out

    script_path = (PROJECT_DIR / script).resolve()
    if not script_path.is_file():
        out["status"] = "missing"
        out["detail"] = f"script file not found: {script}"
        return out

    env = {**os.environ, "HOOK_DRYRUN": "1"}
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            input="{}",
            text=True,
            capture_output=True,
            timeout=HOOK_TIMEOUT_S,
            env=env,
            cwd=str(PROJECT_DIR),
            check=False,
        )
    except subprocess.TimeoutExpired:
        out["status"] = "timeout"
        out["detail"] = f"exceeded {HOOK_TIMEOUT_S}s"
        return out
    except OSError as e:
        out["status"] = "error"
        out["detail"] = f"could not invoke: {e}"
        return out

    if result.returncode != 0:
        out["status"] = "failed"
        tail = (result.stderr or result.stdout or "").strip().splitlines()[-3:]
        out["detail"] = f"exit={result.returncode}; " + " | ".join(tail) if tail else f"exit={result.returncode}"
        return out

    out["status"] = "ok"
    return out


def write_audit_event(results: list[dict], overall: str) -> None:
    failed = [r for r in results if r["status"] not in ("ok", "skipped")]
    entry = {
        "timestamp": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "hook_health_check",
        "status": overall,                # "ok" | "degraded"
        "checked": len(results),
        "failed_hooks": [
            {"event": r["event"], "script": r["script"], "status": r["status"], "detail": r["detail"]}
            for r in failed
        ],
    }
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"⚠️  Could not append to {AUDIT_LOG}: {e}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Hook health-check (v2.2).")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Print one line per probed hook (default: only failures).")
    args = p.parse_args(argv)

    try:
        records = discover_hooks()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"❌ Could not read {SETTINGS}: {e}", file=sys.stderr)
        return 2

    if not records:
        print("⚠️  No hooks declared in .claude/settings.json::hooks", file=sys.stderr)
        write_audit_event([], "ok")
        return 0

    results = [probe_hook(r) for r in records]
    failed = [r for r in results if r["status"] not in ("ok", "skipped")]
    overall = "ok" if not failed else "degraded"

    print(f"=== Hook health-check ({len(results)} probed) ===")
    if args.verbose:
        for r in results:
            icon = {"ok": "✅", "skipped": "⚪", "missing": "❌", "failed": "❌",
                    "timeout": "⏱️", "error": "❌"}.get(r["status"], "❓")
            label = f"{r['event']}" + (f" [{r['matcher']}]" if r['matcher'] else "")
            print(f"  {icon} {label:<24} {r['script']}  ({r['status']})")
            if r["detail"]:
                print(f"     → {r['detail']}")
    else:
        for r in failed:
            print(f"  ❌ {r['event']} → {r['script']} ({r['status']})", file=sys.stderr)
            if r["detail"]:
                print(f"     → {r['detail']}", file=sys.stderr)

    print(f"Overall: {'🟢 ok' if overall == 'ok' else '🔴 degraded'}  "
          f"(ok={len([r for r in results if r['status'] == 'ok'])}, "
          f"failed={len(failed)})")

    write_audit_event(results, overall)
    return 0 if overall == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
