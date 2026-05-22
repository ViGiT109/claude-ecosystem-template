#!/usr/bin/env python3
"""
Синхронизация AI-инфраструктуры из шаблона-апстрима в конечный проект.

Копирует `.claude/`, `.agents/`, `scripts/` и корневой `AGENTS.md` из
шаблона в проект. Никогда не трогает `.memory/`, `.env*`, `task.md`,
`.git/`, `.venv/`.

По умолчанию — холостой прогон (только печатает план). Запись — с `--apply`.

Использование:
    python scripts/update_ecosystem.py --from <путь-или-git-url>
    python scripts/update_ecosystem.py --from <путь> --apply
    python scripts/update_ecosystem.py --from <путь> --apply --exclude '.claude/skills/*'
    python scripts/update_ecosystem.py --from <путь> --apply --force
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    print("ERROR: требуется Python 3.11+ (нужен модуль tomllib)", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Конфигурация: что синхронизируем, что не трогаем

SYNC_DIRS = (".claude", ".agents", "scripts")
SYNC_FILES = ("AGENTS.md",)
PROTECTED_PATHS = (
    ".memory",
    ".env",
    "task.md",
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".ecosystem.toml",
)


# ---------------------------------------------------------------------------
# Структуры


@dataclass
class FileEntry:
    relpath: str
    status: str          # new | modified | unchanged | blocked
    upstream_sha: str
    local_sha: str | None
    note: str = ""


# ---------------------------------------------------------------------------
# Вспомогательные функции


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_protected(relpath: str) -> bool:
    parts = Path(relpath).parts
    if not parts:
        return False
    head = parts[0]
    if head in {".memory", ".git", ".venv", "node_modules", "__pycache__"}:
        return True
    if head == "task.md":
        return True
    if head == ".ecosystem.toml":
        return True
    if head.startswith(".env"):
        return True
    return False


def matches_exclude(relpath: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relpath, p) for p in patterns)


def resolve_upstream(source: str) -> tuple[Path, Path | None]:
    """Возвращает (путь_к_шаблону, путь_temp_dir_для_удаления_или_None)."""
    p = Path(source)
    if p.exists() and p.is_dir():
        return p.resolve(), None

    # Иначе считаем, что это git-URL
    tmp = Path(tempfile.mkdtemp(prefix="ecosystem-upstream-"))
    print(f"→ Клонирую {source} во временный каталог...", file=sys.stderr)
    result = subprocess.run(
        ["git", "clone", "--depth=1", source, str(tmp)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"ERROR: git clone не удался:\n{result.stderr}", file=sys.stderr)
        sys.exit(2)
    return tmp, tmp


def looks_like_template(root: Path) -> bool:
    return (root / ".claude").is_dir() or (root / ".agents").is_dir()


def collect_upstream_files(upstream: Path) -> list[str]:
    """Все файлы из шаблона, которые подлежат синхронизации (отн. пути)."""
    out: list[str] = []
    for d in SYNC_DIRS:
        src = upstream / d
        if not src.is_dir():
            continue
        for f in src.rglob("*"):
            if not f.is_file():
                continue
            rel = f.relative_to(upstream).as_posix()
            # Игнорируем мусор внутри синхронизируемых каталогов
            if any(part in {"__pycache__", ".pytest_cache"} for part in f.parts):
                continue
            if f.name.endswith((".pyc", ".pyo")):
                continue
            out.append(rel)
    for name in SYNC_FILES:
        if (upstream / name).is_file():
            out.append(name)
    return sorted(out)


def read_local_shas(project: Path) -> dict[str, str]:
    """Читает прошлый слепок контрольных сумм из .ecosystem.toml."""
    cfg = project / ".ecosystem.toml"
    if not cfg.is_file():
        return {}
    try:
        with cfg.open("rb") as f:
            data = tomllib.load(f)
    except Exception:
        return {}
    eco = data.get("ecosystem") or {}
    shas = eco.get("file_shas") or {}
    return {str(k): str(v) for k, v in shas.items() if isinstance(v, str)}


def write_ecosystem_section(
    project: Path,
    upstream_version: str | None,
    upstream_sha: str | None,
    file_shas: dict[str, str],
) -> None:
    """Дописывает или заменяет секцию [ecosystem] в .ecosystem.toml.

    Простая текстовая замена: если секция уже есть — режем её до следующего
    `[...]` заголовка и подставляем новую. Если нет — дописываем в конец.
    """
    cfg = project / ".ecosystem.toml"
    text = cfg.read_text(encoding="utf-8") if cfg.is_file() else ""

    lines = text.splitlines()
    start = None
    end = len(lines)
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("[ecosystem]") or s.startswith("[ecosystem."):
            if start is None:
                start = i
        elif start is not None and s.startswith("[") and not s.startswith("[ecosystem"):
            end = i
            break

    new_block: list[str] = []
    new_block.append("[ecosystem]")
    if upstream_version:
        new_block.append(f'version = "{upstream_version}"')
    if upstream_sha:
        new_block.append(f'upstream_sha = "{upstream_sha}"')
    new_block.append("")
    new_block.append("[ecosystem.file_shas]")
    for path in sorted(file_shas):
        new_block.append(f'"{path}" = "{file_shas[path]}"')
    new_block.append("")

    if start is not None:
        new_lines = lines[:start] + new_block + lines[end:]
    else:
        new_lines = lines[:]
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        new_lines += new_block

    cfg.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def get_upstream_head(upstream: Path) -> str | None:
    """Короткий sha HEAD шаблона, если это git-репозиторий."""
    if not (upstream / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(upstream), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() or None if result.returncode == 0 else None


def get_upstream_version(upstream: Path) -> str | None:
    """Версия из plugin.json шаблона, если найдём."""
    pj = upstream / "plugin.json"
    if not pj.is_file():
        return None
    import json
    try:
        return json.loads(pj.read_text(encoding="utf-8")).get("version")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Основная логика


def build_plan(
    upstream: Path,
    project: Path,
    exclude_patterns: list[str],
    force: bool,
) -> list[FileEntry]:
    snapshot_shas = read_local_shas(project)
    entries: list[FileEntry] = []

    for rel in collect_upstream_files(upstream):
        if is_protected(rel):
            continue
        if matches_exclude(rel, exclude_patterns):
            continue

        upstream_file = upstream / rel
        local_file = project / rel
        upstream_sha = sha256_of(upstream_file)

        if not local_file.exists():
            entries.append(FileEntry(rel, "new", upstream_sha, None))
            continue

        local_sha = sha256_of(local_file)
        if local_sha == upstream_sha:
            entries.append(FileEntry(rel, "unchanged", upstream_sha, local_sha))
            continue

        # Локальный отличается от шаблона. Был ли он отредактирован вручную?
        snap = snapshot_shas.get(rel)
        hand_edited = snap is not None and local_sha != snap and local_sha != upstream_sha
        if hand_edited and not force:
            entries.append(
                FileEntry(
                    rel,
                    "blocked",
                    upstream_sha,
                    local_sha,
                    note="ручная правка — нужен --force",
                )
            )
        else:
            entries.append(FileEntry(rel, "modified", upstream_sha, local_sha))

    return entries


def print_plan(entries: list[FileEntry], apply: bool) -> None:
    if not entries:
        print("Нечего синхронизировать — шаблон пуст или всё исключено.")
        return

    by_status: dict[str, list[FileEntry]] = {}
    for e in entries:
        by_status.setdefault(e.status, []).append(e)

    header = "ПЛАН СИНХРОНИЗАЦИИ" if apply else "ХОЛОСТОЙ ПРОГОН (без записи)"
    print(f"\n=== {header} ===\n")

    order = ("new", "modified", "blocked", "unchanged")
    labels = {
        "new":       "Новые файлы",
        "modified":  "Будут перезаписаны",
        "blocked":   "Заблокированы (ручная правка)",
        "unchanged": "Без изменений",
    }

    for status in order:
        items = by_status.get(status, [])
        if not items:
            continue
        print(f"-- {labels[status]} ({len(items)}) --")
        for e in items:
            extra = f"   [{e.note}]" if e.note else ""
            print(f"  {e.relpath}{extra}")
        print()

    counts = {s: len(by_status.get(s, [])) for s in order}
    print(
        f"Итого: новых={counts['new']}  "
        f"изменённых={counts['modified']}  "
        f"заблокированных={counts['blocked']}  "
        f"без изменений={counts['unchanged']}"
    )

    if not apply:
        print("\nЭто холостой прогон. Для записи добавь --apply.")


def apply_plan(
    entries: list[FileEntry],
    upstream: Path,
    project: Path,
) -> tuple[int, int]:
    """Возвращает (записано, пропущено_заблокированных)."""
    written = 0
    blocked = 0
    for e in entries:
        if e.status == "blocked":
            blocked += 1
            continue
        if e.status == "unchanged":
            continue
        src = upstream / e.relpath
        dst = project / e.relpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        written += 1
    return written, blocked


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Синхронизация AI-инфраструктуры шаблона в проект.",
    )
    p.add_argument(
        "--from",
        dest="source",
        required=True,
        help="Путь к локальному шаблону или git-URL для клонирования",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="Применить изменения (по умолчанию — холостой прогон).",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Маска путей для исключения (можно повторять). Пример: '.claude/skills/*'.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Перезаписать даже файлы с ручными правками.",
    )
    p.add_argument(
        "--project",
        default=".",
        help="Корень проекта-получателя (по умолчанию — текущий каталог).",
    )

    args = p.parse_args(argv)

    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"ERROR: каталог проекта не найден: {project}", file=sys.stderr)
        return 2

    upstream, tmp_dir = resolve_upstream(args.source)
    try:
        if not looks_like_template(upstream):
            print(
                f"ERROR: {upstream} не похож на шаблон экосистемы "
                "(нет .claude/ и .agents/)",
                file=sys.stderr,
            )
            return 2

        entries = build_plan(upstream, project, args.exclude, args.force)
        print_plan(entries, args.apply)

        blocked_count = sum(1 for e in entries if e.status == "blocked")
        if args.apply and blocked_count and not args.force:
            print(
                f"\nПрервано: {blocked_count} файл(ов) с ручными правками. "
                "Запусти с --force, чтобы перезаписать.",
                file=sys.stderr,
            )
            return 1

        if args.apply:
            written, blocked = apply_plan(entries, upstream, project)
            # Слепок контрольных сумм — записываем все non-blocked файлы шаблона
            new_shas = {
                e.relpath: e.upstream_sha
                for e in entries
                if e.status != "blocked"
            }
            # Сохраняем старые слепки заблокированных, чтобы не потерять их
            old_shas = read_local_shas(project)
            for e in entries:
                if e.status == "blocked" and e.relpath in old_shas:
                    new_shas[e.relpath] = old_shas[e.relpath]

            write_ecosystem_section(
                project,
                upstream_version=get_upstream_version(upstream),
                upstream_sha=get_upstream_head(upstream),
                file_shas=new_shas,
            )
            print(f"\nГотово. Записано файлов: {written}. Пропущено: {blocked}.")

        return 0
    finally:
        if tmp_dir is not None:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
