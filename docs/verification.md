# Release Verification

This page records the checks performed for version `0.1.0` before its initial public push on 2026-08-11.

## Offline verification

| Check | Result |
|---|---|
| Unit and end-to-end tests | Passed |
| Ruff static/lint checks | Passed |
| Public-surface credential/path/binary scan | Passed |
| JSON syntax validation | Passed |
| YAML/CFF syntax parsing | Passed |
| Local Markdown target validation | Passed |
| Editable installation in an isolated environment | Passed |
| Wheel build | Passed |
| Synthetic CLI workflow | Passed with explicit non-formal status |

The synthetic workflow produced four source-local F-D-G candidates, completed the selector–critic–synthesis trace, recorded a scoped human approval, and ended with:

```text
SYNTHETIC_ESTIMATE_NOT_FORMAL_RELEASE
```

## Live public-source integration check

On 2026-08-11, the release candidate performed one opt-in retrieval from the public NNDC ENSDF interface for `102Mo`, limited to one returned dataset. The client recorded:

- dataset record: `102042001,102MO`;
- title: `ADOPTED LEVELS, GAMMAS`;
- upstream revision text: `2009-08`;
- returned ENSDF byte count: `25110`; and
- returned content SHA-256: `35b6ce74200647d4aadfe3d0839d702cc000b6bc0e9246ae3095beb6e0727a03`.

The documented subset parser then reported 66 levels, 57 gamma transitions, and 56 transitions placed by energy closure. The fetched file and manifest were kept outside the repository and are not redistributed.

This check establishes that the retrieval and subset-parser integration worked against the live upstream response on that date. It does not freeze the database, validate the evaluation, or establish a scientific result. Upstream content and interfaces can change.

## Reproduce the public checks

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest
python tools/public_surface_audit.py
anspec demo --config configs/demo_workflow.json --output demo-output
```

The live check is intentionally separate because it uses the network and current upstream state:

```bash
anspec fetch-ensdf \
  --nucleus 102Mo \
  --source ensdf \
  --limit 1 \
  --output-dir local-data/102Mo
```

Review and cite the returned evaluation according to current NNDC guidance. Do not add `local-data/` to the public repository without a separate rights and governance review.
