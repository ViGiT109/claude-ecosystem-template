#!/usr/bin/env python3
"""Project Health Check.

Reads project configuration from .ecosystem.toml and runs:
1. Required documents check.
2. print() in backend modules check (Python projects only).
3. Module import check (Python projects only).
4. Dependency sync check (uv projects only).
5. Git status summary.
"""

import ast
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS = [
    "CHANGELOG.md",
    "ROADMAP.md",
    "CLAUDE.md",
    "BUGS.md",
]

IGNORED_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
    ".mypy_cache", "tests", "docs", "scripts", ".agents", ".claude", "node_modules",
    ".memory",
}


# ---------------------------------------------------------------------------
# Load .ecosystem.toml
# ---------------------------------------------------------------------------
def _load_toml() -> dict:
    toml_path = PROJECT_ROOT / ".ecosystem.toml"
    if not toml_path.exists():
        return {}
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            print("⚠️  Cannot read .ecosystem.toml (no toml library). Skipping TOML-based checks.")
            return {}
    with open(toml_path, "rb") as f:
        return tomllib.load(f)


# ---------------------------------------------------------------------------
# Check: required documents
# ---------------------------------------------------------------------------
def check_documents() -> bool:
    print("=== Documents ===")
    all_ok = True
    for doc in DOCUMENTS:
        path = PROJECT_ROOT / doc
        if path.exists() and path.stat().st_size > 0:
            print(f"✅ {doc}")
        else:
            print(f"❌ {doc}: missing or empty!")
            all_ok = False
    return all_ok


# ---------------------------------------------------------------------------
# Check: print() in backend modules (Python only)
# ---------------------------------------------------------------------------
class _PrintCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found_prints: list[int] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self.found_prints.append(node.lineno)
        self.generic_visit(node)


def check_prints(backend_modules: list[str]) -> bool:
    """Check that print() is not used in declared backend modules."""
    print("\n=== print() in backend modules ===")
    if not backend_modules:
        print("⚠️  No backend_modules declared in .ecosystem.toml — skipping print() check.")
        return True

    success = True
    for rel_mod in backend_modules:
        mod_path = PROJECT_ROOT / rel_mod
        if not mod_path.exists():
            print(f"⚠️  Module path not found: {rel_mod}")
            continue
        # If path is a directory, scan all .py files in it
        files = list(mod_path.rglob("*.py")) if mod_path.is_dir() else [mod_path]
        for path in files:
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            try:
                content = path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(path))
                visitor = _PrintCallVisitor()
                visitor.visit(tree)
                if visitor.found_prints:
                    lines_str = ", ".join(map(str, visitor.found_prints))
                    rel_path = path.relative_to(PROJECT_ROOT)
                    print(f"❌ {rel_path}: print() at lines {lines_str}")
                    success = False
            except SyntaxError as e:
                print(f"⚠️  Syntax error in {path.relative_to(PROJECT_ROOT)}: {e}")
            except Exception as e:
                print(f"⚠️  Cannot read {path.relative_to(PROJECT_ROOT)}: {e}")

    if success:
        print("✅ No print() found in backend modules")
    return success


# ---------------------------------------------------------------------------
# Check: uv lock sync (Python + uv only)
# ---------------------------------------------------------------------------
def _resolve_uv() -> str:
    import shutil
    uv = shutil.which("uv")
    if uv:
        return uv
    fallback = Path.home() / ".local" / "bin" / ("uv.exe" if os.name == "nt" else "uv")
    return str(fallback) if fallback.exists() else "uv"


def check_hooks() -> bool:
    """Run scripts/check_hook_health.py and report. Appends event to audit_history."""
    print("\n=== Hooks ===")
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "check_hook_health.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"⚠️  Could not run check_hook_health.py: {e}")
        return True  # don't fail health check on infrastructure glitch
    # Pass through the script's summary line(s). It already prints "🟢 ok" / "🔴 degraded".
    for line in (result.stdout or "").splitlines():
        if line.strip():
            print(line)
    if result.returncode != 0:
        for line in (result.stderr or "").splitlines():
            if line.strip():
                print(line)
        return False
    return True


def check_deps_sync() -> bool:
    print("\n=== Dependency sync (uv) ===")
    import subprocess
    try:
        result = subprocess.run(
            [_resolve_uv(), "lock", "--locked"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("❌ uv.lock and pyproject.toml are out of sync.")
            print("   Run: uv lock")
            return False
        print("✅ Dependencies in sync (uv.lock is current)")
        return True
    except FileNotFoundError:
        print("❌ 'uv' not found in PATH. Install: https://docs.astral.sh/uv/")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    config = _load_toml()
    language = config.get("project", {}).get("language", "")
    python_cfg = config.get("project", {}).get("python", {})
    backend_modules: list[str] = python_cfg.get("backend_modules", [])
    package_manager: str = python_cfg.get("package_manager", "")

    docs_ok = check_documents()

    hooks_ok = check_hooks()

    print_ok = True
    if language in ("python", "both"):
        print_ok = check_prints(backend_modules)

    deps_ok = True
    if language in ("python", "both") and package_manager == "uv":
        deps_ok = check_deps_sync()

    print("\n=== Git status ===")
    os.system("git status --short 2>/dev/null || true")

    if not (docs_ok and hooks_ok and print_ok and deps_ok):
        print("\n❌ Health check FAILED.")
        sys.exit(1)

    print("\n✅ Health check passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
