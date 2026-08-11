#!/usr/bin/env python3
"""Fail when a public repository contains common private-workspace residue."""

from __future__ import annotations

import re
import sys
from pathlib import Path

EXCLUDED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "cache",
    "demo-output",
    "dist",
    "downloads",
    "local-data",
}
FORBIDDEN_SUFFIXES = {
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".pptx",
    ".root",
    ".xls",
    ".xlsx",
}
MAX_PUBLIC_FILE_BYTES = 1_000_000
TEXT_SUFFIXES = {
    "",
    ".cff",
    ".ens",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def _patterns() -> list[tuple[str, re.Pattern[str]]]:
    slash = "/"
    return [
        ("private key block", re.compile("BEGIN " + ".*PRIVATE KEY")),
        ("macOS absolute home path", re.compile(re.escape(slash + "Users" + slash))),
        ("Linux absolute home path", re.compile(re.escape(slash + "home" + slash))),
        ("internal server path", re.compile(re.escape(slash + "wuhongyi"))),
        ("unresolved repository owner", re.compile(r"github\.com/OWNER(?:/|$)")),
        (
            "assigned credential-like value",
            re.compile(
                r"(?i)(?:api[_-]?key|access[_-]?token|secret)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}"
            ),
        ),
        ("OpenAI-style token", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{16,}")),
        ("GitHub-style token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}")),
        ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
        (
            "assigned password-like value",
            re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        ),
    ]


def iter_public_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(
            part in EXCLUDED_DIRECTORIES or part.endswith(".egg-info")
            for part in relative_parts
        ):
            continue
        yield path


def audit(root: Path) -> list[str]:
    failures: list[str] = []
    own_path = Path(__file__).resolve()
    for path in iter_public_files(root):
        relative = path.relative_to(root)
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            failures.append(f"forbidden file type: {relative}")
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            failures.append(f"oversized public file: {relative}")
        if path.resolve() == own_path or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            failures.append(f"unexpected binary content: {relative}")
            continue
        for label, pattern in _patterns():
            if pattern.search(text):
                failures.append(f"{label}: {relative}")
    return failures


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    failures = audit(root)
    if failures:
        print("PUBLIC SURFACE AUDIT: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    count = sum(1 for _ in iter_public_files(root))
    print(f"PUBLIC SURFACE AUDIT: PASS ({count} files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
