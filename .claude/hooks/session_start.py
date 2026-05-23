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

# Local sibling import — `_ecosystem_health.py` is in the same directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ecosystem_health as _eh  # noqa: E402

PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", "."))
PLACEHOLDER = "${PROJECT_NAME}"
BOOTSTRAP_SCAN_FILES = ("README.md", "CLAUDE.md", ".ecosystem.toml")
SESSION_START_FILE = PROJECT_DIR / ".memory" / ".session_start"
SESSION_START_REFRESH_HOURS = 12

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
    print(f"Unresolved `{PLACEHOLDER}` placeholder(s) detected in:")
    for name in flagged:
        print(f"  - {name}")
    print()
    print("**Run `.\\bootstrap.ps1` (Windows) or `./bootstrap.sh` before continuing.**")
    print()
    print("Until bootstrap completes the project is not initialised — paths, names,")
    print("and language-specific scaffolding are still in template form.")
    return True


def emit_active_context() -> None:
    path = PROJECT_DIR / ".memory" / "activeContext.md"
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    # First 25 lines typically contain YAML frontmatter + current phase
    head = "\n".join(lines[:25]).rstrip()
    if head:
        print("## 📍 activeContext.md (sprint focus)")
        print(head)
        print()


# NOTE: emit_lessons_freshness() removed in v2.2 Phase 6 — its lessons-freshness
# signal is now part of the unified `## 📊 Ecosystem health` block emitted by
# `emit_ecosystem_health_summary()`. The consolidate-status indicator covers the
# same need (and uses both age and lesson count, which is strictly more
# informative than mtime alone).


def emit_audit_freshness() -> None:
    """Emit an ecosystem-audit freshness marker.

    Three states (computed by `_ecosystem_health.audit_status()`):
    - `required` — 🔴 AUDIT REQUIRED, blocking signal (age ≥ 7 days OR
       ≥ 20 stop_hook events since last audit_complete). The agent should
       launch the `ecosystem-auditor` subagent this turn.
    - `aging`    — 🟡 audit aging, soft warning (3–7 days).
    - `ok`       — silent (no noise on every session start).
    """
    status, reason = _eh.audit_status()
    if status == "required":
        last = _eh.last_audit_info()
        tag = (last or {}).get("tag_under_audit", "")
        window_hint = f"`{tag}..HEAD`" if tag else "`<last_audit_sha>..HEAD`"
        print("## 🔴 AUDIT REQUIRED")
        print(f"- {reason}")
        print(f"- Action: launch `ecosystem-auditor` subagent with window {window_hint}")
        print()
    elif status == "aging":
        print(f"## 📊 audit: 🟡 audit aging — {reason}")
        print()
    # status == "ok" → silent


def emit_promotion_recommendation() -> None:
    """Emit a 🟡 PROMOTE LESSON marker when recurrent lessons await rule promotion.

    v2.3 Phase 3 — detector for the upgrade-path step "lesson → rule" that
    CLAUDE.md prescribes. Scans `.memory/lessons.md` for items whose body
    contains recurrence vocabulary (REPEAT, recurred, 2nd occurrence, ...)
    and whose Source line doesn't already record a promotion. Silent in the
    happy path.
    """
    status, reason = _eh.promotion_status()
    if status != "recommended":
        return
    print(f"## 🟡 PROMOTE LESSON → RULE — {reason}")
    for title in _eh.pending_promotions():
        print(f"- {title}")
    print("- Action: codify in `.agents/rules/*.md`; add a deterministic guardrail")
    print("  if violations recur. Update the lesson's `Source:` line with")
    print("  `promoted to rule` once done so this signal clears.")
    print()


def emit_consolidate_freshness() -> None:
    """Emit a 🟡 CONSOLIDATE RECOMMENDED marker when memory needs a reflective pass.

    Two states (computed by `_ecosystem_health.consolidate_status()`):
    - `recommended` — 🟡 (age ≥ 30 days OR ≥ 20 lessons). Soft signal —
       the agent should run `/consolidate_lessons` when there's a natural
       break in the work. Never blocks.
    - `ok` — silent.
    """
    status, reason = _eh.consolidate_status()
    if status == "recommended":
        print(f"## 🟡 CONSOLIDATE RECOMMENDED — {reason}")
        print("- Action: run `/consolidate_lessons` (or `anthropic-skills:consolidate-memory` skill)")
        print()
    # status == "ok" → silent


def emit_ecosystem_health_summary() -> None:
    """Print the unified `## 📊 Ecosystem health` block (Phase 6 of v2.2).

    Always emitted — one compact table of light-signal indicators that
    summarises the four cardinal axes (audit / lessons / hooks / version
    sync). Action blocks (🔴 AUDIT REQUIRED, 🟡 CONSOLIDATE RECOMMENDED)
    are emitted separately upstream — this block is the at-a-glance
    status, not the call to action.

    Sources of truth come from `_ecosystem_health`; the dashboard
    (`scripts/diag_dashboard.py --summary`) renders the same data, so
    the inject and the CLI agree by construction.
    """
    icon = {
        "ok": "🟢", "aging": "🟡", "required": "🔴",
        "recommended": "🟡", "stale": "🟡", "critical": "🔴",
    }

    audit_status, audit_reason = _eh.audit_status()
    cons_status, cons_reason = _eh.consolidate_status()
    promo_status, promo_reason = _eh.promotion_status()
    hooks_status, hooks_reason = _eh.hook_health_status()

    # Version sync: read three sources and compare. Stdlib only.
    plugin_json = PROJECT_DIR / ".claude-plugin" / "plugin.json"
    changelog = PROJECT_DIR / "CHANGELOG.md"
    pv = cv = None
    if plugin_json.exists():
        try:
            pv = json.loads(plugin_json.read_text(encoding="utf-8")).get("version")
        except (OSError, json.JSONDecodeError):
            pv = None
    if changelog.exists():
        try:
            import re as _re
            for line in changelog.read_text(encoding="utf-8").splitlines():
                m = _re.match(r"^##\s+\[(\d+\.\d+\.\d+)\]", line)
                if m:
                    cv = m.group(1)
                    break
        except OSError:
            pass
    ver_ok = pv is not None and cv is not None and pv == cv
    ver_icon = "🟢" if ver_ok else "🔴"
    ver_note = f"plugin.json={pv}, CHANGELOG={cv}"

    print("## 📊 Ecosystem health")
    print(f"- audit:     {icon.get(audit_status, '❓')} {audit_status} — {audit_reason}")
    print(f"- lessons:   {icon.get(cons_status, '❓')} {cons_status} — {cons_reason}")
    print(f"- promotion: {icon.get(promo_status, '❓')} {promo_status} — {promo_reason}")
    print(f"- hooks:     {icon.get(hooks_status, '❓')} {hooks_status} — {hooks_reason}")
    print(f"- version:   {ver_icon} {'synced' if ver_ok else 'drift'} ({ver_note})")
    print()


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
    print(f"- Estimated context: **{tokens:,} tokens** (~{pct:.0f}% of {model} {window:,})")
    print("- Switching models mid-session does **not** reclaim context — only a new session does.")
    print("- Suggested action: run `/handoff` → start a new session → `/new_session`.")
    print()


def record_session_start() -> None:
    """Stamp the current session start time for finalize_session.py to consume.

    Writes `.memory/.session_start` as single-line JSON `{"started_at": "<ISO UTC>"}`.
    Idempotent within a 12h window — a fresh stamp is only written if the file is
    missing or older than `SESSION_START_REFRESH_HOURS`. This keeps short hook
    reruns (e.g. `/new_session` re-invocations) from clobbering the real start.
    """
    try:
        if SESSION_START_FILE.exists():
            age_h = (dt.datetime.now().timestamp() - SESSION_START_FILE.stat().st_mtime) / 3600
            if age_h < SESSION_START_REFRESH_HOURS:
                return
        SESSION_START_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {"started_at": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
        SESSION_START_FILE.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    except OSError:
        return


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
        print("## 🧹 git: clean (no uncommitted changes)")
    else:
        print(f"## ⚠️ git: {len(lines)} uncommitted change(s)")
        for ln in lines[:10]:
            print(f"  {ln}")
        if len(lines) > 10:
            print(f"  ... and {len(lines) - 10} more")
    print()


def main() -> int:
    # Dry-run mode — used by `scripts/check_hook_health.py` to verify the hook
    # loads without import/syntax errors. Skips inject output and side effects.
    if os.environ.get("HOOK_DRYRUN") == "1":
        return 0

    # Bootstrap guard runs first and short-circuits the normal session preamble.
    if check_bootstrap_done():
        return 0

    payload = _read_stdin_json()
    record_session_start()

    print("# 🚀 Project context (auto-injected by SessionStart hook)")
    print()
    emit_context_window_status(payload)
    emit_active_context()
    # Action blocks (urgent, top-level) come first so the agent doesn't miss them.
    emit_audit_freshness()
    emit_consolidate_freshness()
    emit_promotion_recommendation()
    # Compact health summary — always emitted, mirrors `diag_dashboard.py --summary`.
    emit_ecosystem_health_summary()
    emit_git_status()
    print("_Run `/new_session` to load full context._")
    return 0


if __name__ == "__main__":
    sys.exit(main())
