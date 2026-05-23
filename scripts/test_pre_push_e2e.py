#!/usr/bin/env python3
"""E2E test for the pre-push version-sync guardrail (v2.2.1).

What the v2.2.0 audit caught: a "passes-in-unit-tests-but-fails-in-real-
push" scenario where pre-commit framework silently skipped the hook. This
test exercises the **shim** (`.githooks/pre-push`) — not the script
directly — and verifies the shim's version-check half rejects a wrong-
version tag when invoked the same way git would invoke it (stdin per
`githooks(5)` pre-push protocol).

Scope (deliberately narrow):
    1. Invoke `.githooks/pre-push` directly with a synthetic git pre-push
       stdin payload while a wrong-version tag points at HEAD.
       Expect: non-zero exit and `VERSION SYNC FAILED` on stderr.
    2. Invoke same, with NO wrong tag at HEAD.
       Expect: zero exit (assuming the pre-commit delegation portion
       behaves reasonably; if pre-commit fails for unrelated reasons,
       we explicitly say so).

What this test does NOT cover (intentionally):
- Full `git push` against a bare remote with pre-commit's delegated
  pre-push hooks (ruff, etc.). That requires a fixture repo whose state
  is clean against ruff — out of scope for the version-sync guardrail
  test. A heavier E2E harness can live under `tests/e2e/` later.

Usage:
    python scripts/test_pre_push_e2e.py
    python scripts/test_pre_push_e2e.py --verbose

Exit codes:
    0 — both cases behaved as expected
    1 — at least one case failed
    2 — setup error
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _git(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def read_plugin_version() -> str | None:
    p = Path(".claude-plugin/plugin.json")
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("version")
    except Exception:
        return None


def invoke_shim(stdin_payload: str) -> subprocess.CompletedProcess:
    """Invoke `.githooks/pre-push` directly via sh, with synthetic stdin."""
    return subprocess.run(
        ["sh", ".githooks/pre-push", "origin", "https://example.invalid/dummy.git"],
        input=stdin_payload,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    p = argparse.ArgumentParser(description="E2E test of pre-push version-sync guardrail.")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    # ── Sanity ───────────────────────────────────────────────────────
    if not Path(".githooks/pre-push").is_file():
        print("ERROR: .githooks/pre-push not found.", file=sys.stderr)
        return 2
    plugin_ver = read_plugin_version()
    if not plugin_ver:
        print("ERROR: cannot read plugin.json::version", file=sys.stderr)
        return 2

    head = _git(["rev-parse", "HEAD"]).stdout.strip()
    fake_sha = "abc1234567890123456789012345678901234567"
    # Canonical vX.Y.Z form — TAG_RE only matches strict semver tags so a
    # suffixed tag like v0.0.0-e2e-bad would be IGNORED by the check. Pick
    # a far-future major that no real release would clash with.
    bad_tag = "v99.99.99"

    passed = True

    # ── Case 1: wrong-version tag at HEAD → block ─────────────────────
    _git(["tag", bad_tag])
    try:
        stdin_payload = f"refs/tags/{bad_tag} {head} refs/tags/{bad_tag} {'0' * 40}\n"
        r = invoke_shim(stdin_payload)
        if args.verbose:
            print(f"--- Case 1 ---\nexit={r.returncode}\nstderr tail:\n{r.stderr.strip()[-400:]}\n")
        version_failed = "VERSION SYNC FAILED" in (r.stderr or "")
        if r.returncode != 0 and version_failed:
            print(f"✅ CASE 1 PASS: wrong tag {bad_tag!r} blocked with VERSION SYNC FAILED diagnostic")
        elif r.returncode != 0 and not version_failed:
            print(f"⚠️  CASE 1 PARTIAL: exit={r.returncode} but no VERSION SYNC FAILED diag — block "
                  "may be from another hook (delegated pre-commit run)")
            passed = False
        else:
            print("❌ CASE 1 FAIL: shim exited 0 (expected block) when wrong tag at HEAD")
            passed = False
    finally:
        _git(["tag", "-d", bad_tag])

    # ── Case 2: no wrong-version tag → version check exits 0 ─────────
    # We cannot easily assert "shim exits 0" because pre-commit delegation
    # may exit non-zero on the synthetic remote. Instead: assert that
    # stderr does NOT contain VERSION SYNC FAILED.
    stdin_payload = f"refs/heads/main {head} refs/heads/main {fake_sha}\n"
    r = invoke_shim(stdin_payload)
    if args.verbose:
        print(f"--- Case 2 ---\nexit={r.returncode}\nstderr tail:\n{r.stderr.strip()[-400:]}\n")
    if "VERSION SYNC FAILED" not in (r.stderr or ""):
        print(f"✅ CASE 2 PASS: with no wrong tag at HEAD, version check did not fire "
              f"(shim exit {r.returncode}; non-zero may be unrelated pre-commit delegation)")
    else:
        print("❌ CASE 2 FAIL: version check fired despite no wrong tag at HEAD")
        passed = False

    if passed:
        print("\n🟢 pre-push E2E: OK")
        return 0
    print("\n🔴 pre-push E2E: FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
