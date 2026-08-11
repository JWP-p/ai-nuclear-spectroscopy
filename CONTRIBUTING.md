# Contributing

Thank you for helping make nuclear-spectroscopy workflows more transparent, reusable, and scientifically defensible.

## What makes a useful contribution

Contributions are especially valuable when they:

- preserve source identity and provenance;
- make a scientific assumption explicit and testable;
- add a focused test for a physical or software boundary;
- improve uncertainty reporting without overstating validity;
- improve interoperability with public nuclear-data formats;
- strengthen the human-approval contract for AI-assisted work; or
- make the documentation more useful to researchers outside the original workflow.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
python tools/public_surface_audit.py
```

## Pull-request expectations

1. Open an issue first for changes that alter a physical convention, data model, public API, or scientific status.
2. Keep each pull request focused and include tests for changed behavior.
3. State which evidence supports the change and which limitations remain.
4. Do not upload experimental event files, unpublished spectra, private collaboration material, credentials, or personal paths.
5. Mark synthetic fixtures clearly. Never disguise synthetic or illustrative numbers as measurements.
6. Update documentation and `CHANGELOG.md` for user-visible changes.

## Scientific conventions

Changes to gate direction, timing sign, background subtraction, centroid calculation, PRD calibration, or uncertainty propagation must include:

- the convention in equations or pseudocode;
- at least one deterministic test;
- an explicit statement of the validation scope; and
- review by someone competent in the affected analysis method before formal scientific use.

Passing CI is necessary for merge, but it is not evidence that an experimental lifetime is valid.

## Licensing contributions

By submitting a contribution, you agree that it is your original work or that you have the right to submit it under the Apache License 2.0. Do not copy third-party code, data, figures, or text without compatible permission and attribution.
