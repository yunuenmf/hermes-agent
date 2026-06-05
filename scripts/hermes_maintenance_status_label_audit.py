#!/usr/bin/env python3
"""Audit Hermes Maintenance profile/policy text for canonical Self/Lineage status labels.

The audit intentionally skips runtime history stores (SQLite/session/log/cache files) and
checks policy-like text files that can seed future notifications, prompts, skills,
templates, plans, and watchdog handoffs.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

LEGACY_LABELS = (
    "Coordinator status",
    "PA status",
    "Responsible status",
    "Developer status",
    "Researcher status",
    "Master status",
)

CANONICAL_LABELS = ("Self status:", "Lineage status:")

SKIP_DIR_NAMES = {
    ".git",
    ".local",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "audio_cache",
    "cache",
    "logs",
    "node_modules",
    "sessions",
    "venv",
    ".venv",
}

SKIP_SUFFIXES = {
    ".db",
    ".db-shm",
    ".db-wal",
    ".gif",
    ".jpeg",
    ".jpg",
    ".mp3",
    ".png",
    ".pyc",
    ".sqlite",
    ".sqlite3",
    ".wav",
}


def iter_audit_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if not path.is_file() or path.suffix in SKIP_SUFFIXES:
                continue
            yield path


def audit_path(path: Path) -> list[tuple[int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    findings: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for label in LEGACY_LABELS:
            if label in line:
                findings.append((line_no, label, line.strip()))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        nargs="*",
        type=Path,
        default=[
            Path.home() / ".hermes" / "profiles",
            Path.home() / ".hermes" / "coordination",
        ],
        help="Roots to scan (default: ~/.hermes/profiles ~/.hermes/coordination)",
    )
    args = parser.parse_args()

    failures: list[tuple[Path, int, str, str]] = []
    scanned = 0
    for path in iter_audit_files(args.roots):
        scanned += 1
        for line_no, label, line in audit_path(path):
            failures.append((path, line_no, label, line))

    if failures:
        print("legacy role-specific status labels found:")
        for path, line_no, label, line in failures:
            print(f"{path}:{line_no}: {label}: {line}")
        print(
            "\nExpected notification labels are exactly "
            f"{CANONICAL_LABELS[0]!r} and {CANONICAL_LABELS[1]!r} with "
            "WORKING|WAITING|BLOCKED|DORMANT."
        )
        return 1

    print(
        f"status-label audit passed: scanned {scanned} files; no legacy "
        "role-specific notification labels found."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
