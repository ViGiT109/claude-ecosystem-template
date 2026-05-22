#!/usr/bin/env python3
"""
Session Finalizer — Runtime Guardrail + Memory Reminders + Trajectory Recording.

Ensures:
1. activeContext.md was updated this session
2. No abandoned tasks in task.md
3. Reminder to update progress.md
4. Reminder to update lessons.md
5. Session metrics (quantitative)
6. Trajectory recording (ReasoningBank) → .memory/session_trajectories.jsonl
7. Git commit + push (with pre-commit hooks)

Usage:
    python scripts/finalize_session.py "type(scope): commit message"
"""
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime

CONTEXT_FILE = ".memory/activeContext.md"
LESSONS_FILE = ".memory/lessons.md"
TRAJECTORIES_FILE = ".memory/session_trajectories.jsonl"
AUDIT_HISTORY_FILE = ".memory/audit_history.jsonl"
SESSION_START_FILE = ".memory/.session_start"
REASONING_BANK_SCRIPT = "scripts/reasoning_bank.py"
REASONING_BANK_TIMEOUT_S = 30
REASONING_BANK_OPS = ("ingest_lessons", "ingest_trajectories")


def check_context_freshness() -> None:
    """Verify that activeContext.md was updated this session (within 6 hours)."""
    if os.path.exists(CONTEXT_FILE):
        age_hours = (time.time() - os.path.getmtime(CONTEXT_FILE)) / 3600
        if age_hours > 6:
            print(f"❌ STATE SYNC ERROR: {CONTEXT_FILE} has not been updated in {age_hours:.0f} hours.")
            print("   The agent forgot to sync sprint state!")
            print("   → Update activeContext.md before finalizing!")
            sys.exit(1)
    else:
        print(f"⚠️  WARNING: {CONTEXT_FILE} not found. Skipping freshness check.")


def check_abandoned_tasks() -> None:
    """Scan task.md for unchecked tasks. Block if found."""
    print("⏳ Checking Runtime Guardrail (task completion)...")
    task_files = []
    if os.path.exists("task.md"):
        task_files.append("task.md")

    for tf in task_files:
        try:
            with open(tf, encoding="utf-8") as f:
                for i, line in enumerate(f, 1):
                    if "- [ ]" in line or "- [/]" in line:
                        print("❌ ERROR: Runtime Guardrail triggered! Abandoned tasks found.")
                        print(f"   Unchecked item in {tf} (line {i}): {line.strip()}")
                        print("   → Close all [ ] and [/] in task.md before finalizing!")
                        sys.exit(1)
        except OSError as e:
            print(f"⚠️  Could not read {tf}: {e}")


def check_progress_updates() -> None:
    """Remind to update progress.md if it hasn't changed in 7 days."""
    progress_file = ".memory/progress.md"
    if os.path.exists(progress_file):
        age_days = (time.time() - os.path.getmtime(progress_file)) / 86400
        if age_days > 7:
            print("\n💡 REMINDER: progress.md has not been updated in >7 days.")
            print("   If major milestones were completed — update .memory/progress.md")
    else:
        print("\n⚠️  .memory/progress.md not found!")


def check_lessons_reminder() -> None:
    """Remind to update lessons.md if it hasn't changed in 14 days."""
    if os.path.exists(LESSONS_FILE):
        age_days = (time.time() - os.path.getmtime(LESSONS_FILE)) / 86400
        if age_days > 14:
            print("\n💡 REMINDER: lessons.md has not been updated in >14 days.")
            print("   If errors occurred this session — use /extract_lesson.")
    else:
        print("\n⚠️  .memory/lessons.md not found! Self-Improvement Loop is disabled.")
        print("   Create the file: .memory/lessons.md")


def check_audit_debt() -> None:
    """Warn if no full ecosystem audit (`event: audit_complete`) has run in >14 days.

    We must NOT use the file's mtime: every Claude turn appends a `stop_hook`
    entry to audit_history.jsonl, so mtime is always seconds old. Instead scan
    for entries with `event == "audit_complete"` (written by `/audit_ecosystem`
    Phase E) and take the most recent.
    """
    history_file = ".memory/audit_history.jsonl"
    if not os.path.exists(history_file):
        print("\n⚠️  AUDIT DEBT: audit_history.jsonl not found.")
        print("   No full audit has ever been run.")
        print("   → Run /audit_ecosystem in Claude Code")
        return

    last_complete: datetime | None = None
    try:
        with open(history_file, encoding="utf-8") as fh:
            for raw in fh:
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
                    ts = datetime.fromisoformat(stamp.rstrip("Z"))
                except ValueError:
                    continue
                if last_complete is None or ts > last_complete:
                    last_complete = ts
    except OSError:
        return

    if last_complete is None:
        print("\n⚠️  AUDIT DEBT: no `audit_complete` events recorded.")
        print("   → Run /audit_ecosystem in Claude Code")
        return

    age_days = (datetime.utcnow() - last_complete).days
    if age_days > 14:
        print(f"\n⚠️  AUDIT DEBT: Last ecosystem audit was {age_days} days ago.")
        print("   → Consider running a full audit soon.")


def collect_session_metrics() -> dict:
    """Collect quantitative session metrics (non-blocking)."""
    metrics: dict = {}

    if os.path.exists("task.md"):
        try:
            with open("task.md", encoding="utf-8") as f:
                content = f.read()
            total = content.count("- [")
            done = content.count("- [x]") + content.count("- [X]")
            if total > 0:
                rate = done / total * 100
                metrics["task_completion"] = f"{done}/{total} ({rate:.0f}%)"
        except Exception:
            pass

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().splitlines() if f]
            metrics["files_staged"] = str(len(files))
    except Exception:
        pass

    if os.path.exists(LESSONS_FILE):
        age_days = (time.time() - os.path.getmtime(LESSONS_FILE)) / 86400
        metrics["lessons_age"] = f"{age_days:.1f} days"

    if metrics:
        print("\n📊 Session Metrics:")
        for k, v in metrics.items():
            print(f"   {k}: {v}")

    return metrics


def _tail(text: str, n: int = 5) -> str:
    """Return the last n non-empty lines of `text`, joined with \\n. Truncates to 500 chars."""
    if not text:
        return ""
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines[-n:])[:500]


def _run_ingest_op(op: str) -> dict:
    """Run one ReasoningBank ingest op as a bounded subprocess; return its audit entry.

    Non-blocking by design: ChromaDB may be absent, the script may be slow, the
    user may have nothing to ingest yet. Any of these outcomes is logged but
    never raises into the parent finalize_session.

    Status values:
        - "ok"      — subprocess exit 0
        - "skipped" — subprocess exit non-zero (e.g. chromadb missing)
        - "timeout" — subprocess.TimeoutExpired
        - "error"   — any other exception while invoking
    """
    started = time.time()
    entry: dict = {
        "event": f"reasoning_bank_{op}",
        "timestamp": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    try:
        result = subprocess.run(
            [sys.executable, REASONING_BANK_SCRIPT, op],
            capture_output=True,
            text=True,
            timeout=REASONING_BANK_TIMEOUT_S,
            check=False,
        )
        entry["status"] = "ok" if result.returncode == 0 else "skipped"
        entry["returncode"] = result.returncode
        entry["stdout_tail"] = _tail(result.stdout)
        entry["stderr_tail"] = _tail(result.stderr)
    except subprocess.TimeoutExpired:
        entry["status"] = "timeout"
        entry["returncode"] = None
        entry["stdout_tail"] = ""
        entry["stderr_tail"] = f"timed out after {REASONING_BANK_TIMEOUT_S}s"
    except Exception as e:
        entry["status"] = "error"
        entry["returncode"] = None
        entry["stdout_tail"] = ""
        entry["stderr_tail"] = f"{type(e).__name__}: {e}"

    entry["duration_s"] = round(time.time() - started, 2)

    try:
        with open(AUDIT_HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"⚠️  Could not write reasoning_bank status to {AUDIT_HISTORY_FILE}: {e}")

    status = entry["status"]
    dur = entry["duration_s"]
    label = op.replace("ingest_", "")
    if status == "ok":
        print(f"📚 ReasoningBank {label}: ok ({dur}s)")
    elif status == "skipped":
        hint = entry["stderr_tail"].splitlines()[0] if entry["stderr_tail"] else "non-zero exit"
        print(f"📚 ReasoningBank {label}: skipped — {hint}")
    elif status == "timeout":
        print(f"📚 ReasoningBank {label}: timeout (>{REASONING_BANK_TIMEOUT_S}s) — skipping")
    else:
        print(f"📚 ReasoningBank {label}: error — {entry['stderr_tail']}")

    return entry


def ingest_reasoning_bank() -> dict[str, dict]:
    """Run all ReasoningBank ingest ops (lessons + trajectories) as separate bounded subprocesses.

    Each op writes its own row to `audit_history.jsonl` with a distinct `event`
    (`reasoning_bank_ingest_lessons`, `reasoning_bank_ingest_trajectories`) so
    downstream readers can attribute failures per-collection.
    """
    print()
    return {op: _run_ingest_op(op) for op in REASONING_BANK_OPS}


def _read_session_duration_min() -> float | None:
    """Return minutes since the SessionStart hook stamped `.memory/.session_start`.

    Returns None when the stamp is missing or unreadable — callers store this as
    `null` so consumers can distinguish "unknown" from "0 minutes".
    """
    if not os.path.exists(SESSION_START_FILE):
        return None
    try:
        with open(SESSION_START_FILE, encoding="utf-8") as f:
            payload = json.load(f)
        started_at = payload.get("started_at")
        if not started_at:
            return None
        ts = datetime.fromisoformat(started_at.rstrip("Z")).replace(tzinfo=UTC)
        delta_s = (datetime.now(tz=UTC) - ts).total_seconds()
        return round(max(0.0, delta_s / 60), 1)
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _classify_outcome(task_completion: str) -> str:
    """Map a "done/total (pct%)" string to one of success/partial-success/partial-failure/unknown."""
    if not task_completion or task_completion == "N/A":
        return "unknown"
    try:
        rate = int(task_completion.split("(")[1].rstrip("%)"))
    except (IndexError, ValueError):
        return "unknown"
    if rate == 100:
        return "success"
    if rate >= 70:
        return "partial-success"
    return "partial-failure"


def record_session_trajectory(commit_msg: str, metrics: dict) -> None:
    """Append session trajectory to JSONL with the v2.1 expanded schema.

    Schema (spec L131): date, commit_msg, outcome, task_completion, files_touched,
    duration_min, tools_used. Backward-compatible — older rows missing fields are
    still parsed defensively in `reasoning_bank.parse_trajectories()`.
    """
    task_completion = metrics.get("task_completion", "N/A")

    files_touched: list[str] = []
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            files_touched = [f for f in result.stdout.strip().splitlines() if f]
    except Exception:
        files_touched = []

    trajectory = {
        "date": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "commit_msg": commit_msg,
        "outcome": _classify_outcome(task_completion),
        "task_completion": task_completion,
        "files_touched": files_touched,
        "duration_min": _read_session_duration_min(),
        # Placeholder — no in-process aggregator wires up tool counts yet.
        # Not gated by Phase 2 acceptance criteria; keeps schema forward-compatible.
        "tools_used": [],
    }

    try:
        with open(TRAJECTORIES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(trajectory, ensure_ascii=False) + "\n")
        print(f"\n📝 Trajectory recorded → {TRAJECTORIES_FILE}")
    except Exception as e:
        print(f"\n⚠️  Trajectory recording failed (non-blocking): {e}")


def _get_worktree_info() -> tuple[str | None, str | None]:
    """Return (main worktree path, current branch) if in a worktree, else (None, None)."""
    r = subprocess.run(["git", "worktree", "list", "--porcelain"], capture_output=True, text=True)
    if r.returncode != 0:
        return None, None
    lines = r.stdout.splitlines()
    worktrees: list[dict] = []
    current: dict = {}
    for line in lines:
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[9:]}
        elif line.startswith("branch "):
            current["branch"] = line[7:].split("/")[-1]
    if current:
        worktrees.append(current)

    if len(worktrees) < 2:
        return None, None

    main_path = worktrees[0]["path"]
    cwd = os.path.realpath(os.getcwd())
    for wt in worktrees[1:]:
        if os.path.realpath(wt["path"]) == cwd:
            return main_path, wt.get("branch")
    return None, None


def _merge_to_main(main_path: str, branch: str) -> None:
    """Fast-forward merge current branch into main worktree and push."""
    print(f"⏳ FF-merge '{branch}' → main (so next sessions see progress)...")
    stash_r = subprocess.run(
        ["git", "-C", main_path, "stash", "--include-untracked"],
        capture_output=True, text=True,
    )
    stashed = stash_r.returncode == 0 and "No local changes" not in stash_r.stdout

    r = subprocess.run(
        ["git", "-C", main_path, "merge", "--ff-only", branch],
        capture_output=True, text=True,
    )
    if stashed:
        subprocess.run(["git", "-C", main_path, "stash", "pop"], capture_output=True)

    if r.returncode != 0:
        print(f"⚠️  FF-merge failed (skipping): {r.stderr.strip()}")
        return

    push_r = subprocess.run(
        ["git", "-C", main_path, "push", "origin", "main"],
        capture_output=True, text=True,
    )
    if push_r.returncode == 0:
        print("✅ main updated — next session will pick up progress automatically.")
    else:
        print(f"⚠️  Push main failed: {push_r.stderr.strip()}")


def git_commit_push(commit_msg: str) -> None:
    """Run git commit (with pre-commit hooks), push, and update main if in worktree."""
    print("⏳ Creating commit (pre-commit hooks active)...")
    result = subprocess.run(["git", "commit", "-m", commit_msg])
    if result.returncode != 0:
        print("⚠️  Commit not created (possibly nothing to commit).")
    else:
        print("⏳ Pushing to remote...")
        subprocess.run(["git", "push"], check=False)
        main_path, branch = _get_worktree_info()
        if main_path and branch:
            _merge_to_main(main_path, branch)


def main() -> None:
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("❌ ERROR: Commit message not provided!")
        print('   Usage: python scripts/finalize_session.py "type(scope): message"')
        sys.exit(1)

    commit_msg = sys.argv[1].strip()

    check_context_freshness()
    check_abandoned_tasks()

    print(f"✅ State Management: Basic checks passed. Commit message: '{commit_msg}'")

    check_progress_updates()
    check_lessons_reminder()
    check_audit_debt()

    print("\n⏳ Staging files...")
    subprocess.run(["git", "add", "."], check=True)

    metrics = collect_session_metrics()
    ingest_reasoning_bank()
    record_session_trajectory(commit_msg, metrics)
    git_commit_push(commit_msg)

    print("\n🎉 SESSION EXPLICITLY FINALIZED!")


if __name__ == "__main__":
    main()
