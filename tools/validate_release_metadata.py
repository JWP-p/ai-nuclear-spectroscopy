#!/usr/bin/env python3
"""Check that the public version markers agree before a release or merge."""

import pathlib
import re
import sys


VERSION_RE = re.compile(r'^version:\s*["\']?([^"\'\s]+)', re.MULTILINE)
INIT_VERSION_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def validate(root: pathlib.Path) -> list[str]:
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(
        r"(?ms)^\[project\].*?^version\s*=\s*[\"']([^\"']+)[\"']",
        pyproject,
    )
    if not version_match:
        return ["pyproject.toml has no project version"]
    project_version = version_match.group(1)
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
            "CITATION.cff version "
            f"{citation_match.group(1)!r} != project version {project_version!r}"
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
    root = pathlib.Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print("RELEASE METADATA: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(
        r"(?ms)^\[project\].*?^version\s*=\s*[\"']([^\"']+)[\"']",
        pyproject,
    ).group(1)
    print(f"RELEASE METADATA: PASS (version {version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
