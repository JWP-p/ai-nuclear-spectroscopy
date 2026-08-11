# Complete synthetic workflow

Run from the repository root:

```bash
python -m ai_nuclear_spectroscopy demo \
  --config configs/demo_workflow.json \
  --output demo-output
```

The command creates:

- `workflow_result.json`: machine-readable decisions and calculations;
- `workflow_report.md`: a short human-readable review surface;
- `provenance_manifest.json`: input and output hashes with data classification.

Every nucleus, level, transition, count, spectrum, PRD parameter, and lifetime in
this example is fictional. The example demonstrates software behavior and
stage boundaries; it is not a nuclear-data evaluation or experimental result.
