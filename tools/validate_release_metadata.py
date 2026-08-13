#!/usr/bin/env python3
"""Check that the public version markers agree before a release or merge."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


VERSION_RE = re.compile(r'^version:\s*["\']?([^"\'\s]+)', re.MULTILINE)
INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def validate(root: Path) -> list[str]:
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = str(pyproject["project"]["version"])
    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    init = (root / "src" / "ai_nuclear_spectroscopy" / "__init__.py").read_text(
        encoding="utf-8"
    )

    errors: list[str] = []
    citation_match = VERSION_RE.search(citation)
    init_match = INIT_VERSION_RE.search(init)
    if not citation_match:
        errors.append("CITATION.cff has no version field")
    elif citation_match.group(1) != project_version:
        errors.append(
            f"CITATION.cff version {citation_match.group(1)!r} != project version {project_version!r}"
        )
    if not init_match:
        errors.append("package __version__ is missing")
    elif init_match.group(1) != project_version:
        errors.append(
            f"package __version__ {init_match.group(1)!r} != project version {project_version!r}"
        )
    if f"## [{project_version}]" not in changelog:
        errors.append(f"CHANGELOG.md has no release heading for {project_version}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print("RELEASE METADATA: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    print(f"RELEASE METADATA: PASS (version {version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
