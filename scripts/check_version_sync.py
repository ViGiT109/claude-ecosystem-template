#!/usr/bin/env python3
"""Version-sync guardrail.

Checks that the project version is consistent across:
- `.claude-plugin/plugin.json::version` (source of truth)
- Latest `## [X.Y.Z]` header in `CHANGELOG.md`
- `.ecosystem.toml::ecosystem.version` (if the section exists)
- Any tag of the form `vX.Y.Z` being pushed (only in `--pre-push` mode,
  consumes git's pre-push stdin protocol)

Exits 1 with a diagnostic list to stderr on any drift; exit 0 otherwise.

Usage
-----
Standalone check (run any time; no stdin needed):

    python scripts/check_version_sync.py

Pre-push hook mode (called by git via pre-commit framework with stdin
formatted per `githooks(5)` — one line per ref: `<local_ref> <local_sha>
<remote_ref> <remote_sha>`):

    python scripts/check_version_sync.py --pre-push

Registered as a `pre-push` hook via `.pre-commit-config.yaml`
(`stages: [pre-push]`). Install with::

    pre-commit install --hook-type pre-push
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    print("ERROR: requires Python 3.11+ (need tomllib)", file=sys.stderr)
    sys.exit(2)


PLUGIN_JSON = Path(".claude-plugin/plugin.json")
CHANGELOG = Path("CHANGELOG.md")
ECOSYSTEM_TOML = Path(".ecosystem.toml")

TAG_RE = re.compile(r"^v(\d+\.\d+\.\d+)$")
CHANGELOG_HEADER_RE = re.compile(r"^##\s+\[(\d+\.\d+\.\d+)\]")


def read_plugin_version() -> str | None:
    if not PLUGIN_JSON.is_file():
        return None
    try:
        return json.loads(PLUGIN_JSON.read_text(encoding="utf-8")).get("version")
    except Exception:
        return None


def read_latest_changelog_version() -> str | None:
    """First `## [X.Y.Z]` header (skips `[Unreleased]`)."""
    if not CHANGELOG.is_file():
        return None
    for line in CHANGELOG.read_text(encoding="utf-8").splitlines():
        m = CHANGELOG_HEADER_RE.match(line)
        if m:
            return m.group(1)
    return None


def read_ecosystem_version() -> str | None:
    """Returns None if file or `[ecosystem]` section is missing — not an error."""
    if not ECOSYSTEM_TOML.is_file():
        return None
    try:
        with ECOSYSTEM_TOML.open("rb") as f:
            data = tomllib.load(f)
    except Exception:
        return None
    eco = data.get("ecosystem") or {}
    v = eco.get("version")
    return str(v) if isinstance(v, str) else None


def read_pushed_tags() -> list[str]:
    """Return tag names being considered for push.

    Strategy (in order):
    1. `git tag --points-at HEAD` — primary source. Catches the canonical
       release flow `git push --follow-tags` because the new tag points
       at the just-committed HEAD. Works regardless of how the hook is
       invoked (raw git hook, pre-commit framework wrapper, manual CLI).
       Added in v2.2.1 after the v2.2.0 audit found that pre-commit
       framework on Windows silently passes pre-push hooks without
       executing the script — making stdin parsing alone unreliable.
    2. Git's pre-push stdin (`<local_ref> <local_sha> <remote_ref>
       <remote_sha>`), if non-empty. Only populated when the hook is run
       as a raw `.git/hooks/pre-push` and the caller did not redirect
       stdin. Kept for direct-invocation unit tests.

    Deletions (local_sha = 40 zeros) are skipped — nothing to verify.
    """
    tags: list[str] = []

    # (1) Tags pointing at HEAD — primary, framework-independent.
    try:
        r = subprocess.run(
            ["git", "tag", "--points-at", "HEAD"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if r.returncode == 0:
            tags.extend(t.strip() for t in r.stdout.splitlines() if t.strip())
    except (OSError, subprocess.TimeoutExpired):
        pass

    # (2) Stdin (pre-push protocol). Only effective when invoked raw.
    if not sys.stdin.isatty():
        try:
            for raw in sys.stdin:
                parts = raw.strip().split()
                if len(parts) < 4:
                    continue
                local_ref, local_sha = parts[0], parts[1]
                if local_sha == "0" * 40:
                    continue  # deletion — skip
                if local_ref.startswith("refs/tags/"):
                    tag = local_ref[len("refs/tags/"):]
                    if tag not in tags:
                        tags.append(tag)
        except Exception:
            pass

    return tags


def main(argv: list[str]) -> int:
    pre_push = "--pre-push" in argv

    plugin_ver = read_plugin_version()
    changelog_ver = read_latest_changelog_version()
    ecosystem_ver = read_ecosystem_version()

    problems: list[str] = []

    if plugin_ver is None:
        problems.append("plugin.json not found or version missing")

    if plugin_ver and changelog_ver is None:
        problems.append("CHANGELOG.md has no ## [X.Y.Z] header (cannot verify)")
    elif plugin_ver and changelog_ver and plugin_ver != changelog_ver:
        problems.append(
            f"plugin.json::version = {plugin_ver!r} but latest CHANGELOG header = [{changelog_ver}]"
        )

    if plugin_ver and ecosystem_ver and ecosystem_ver != plugin_ver:
        problems.append(
            f"plugin.json::version = {plugin_ver!r} but "
            f".ecosystem.toml::ecosystem.version = {ecosystem_ver!r}"
        )

    if pre_push and plugin_ver:
        for tag in read_pushed_tags():
            m = TAG_RE.match(tag)
            if not m:
                continue  # non-semver tag (e.g. release-candidate marker) — ignore
            tag_ver = m.group(1)
            if tag_ver != plugin_ver:
                problems.append(
                    f"pushed tag {tag!r} does not match plugin.json::version = {plugin_ver!r}"
                )

    if problems:
        print("❌ VERSION SYNC FAILED — push/check blocked!", file=sys.stderr)
        for p in problems:
            print(f"  • {p}", file=sys.stderr)
        print(
            "\nRules:\n"
            "  - plugin.json::version is the source of truth.\n"
            "  - CHANGELOG.md latest ## [X.Y.Z] must match.\n"
            "  - .ecosystem.toml::ecosystem.version (if set) must match.\n"
            "  - Pushed tags of the form vX.Y.Z must match plugin.json::version.\n"
            "\nTypical fix:\n"
            "  1. Set the new version in .claude-plugin/plugin.json.\n"
            "  2. Add CHANGELOG.md ## [X.Y.Z] — YYYY-MM-DD header.\n"
            "  3. Run: python scripts/update_ecosystem.py --from . --apply (syncs .ecosystem.toml).\n"
            "  4. If a tag was already created with the wrong version:\n"
            "       git tag -d vX.Y.Z && git tag -a vX.Y.Z -m '...'\n",
            file=sys.stderr,
        )
        return 1

    if not pre_push:
        # Standalone mode: print a friendly OK summary so the script is useful
        # for ad-hoc verification.
        print("✅ Versions in sync.")
        print(f"  plugin.json:    {plugin_ver}")
        print(f"  CHANGELOG.md:   {changelog_ver}")
        if ecosystem_ver is not None:
            print(f"  .ecosystem.toml: {ecosystem_ver}")
        else:
            print("  .ecosystem.toml: (no [ecosystem] section — skipped)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
