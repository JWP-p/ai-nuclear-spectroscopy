# Data Governance

## Public-by-design boundary

The repository is designed to be cloned, inspected, and executed without access to any private experiment. It includes source code, documentation, prompts, configurations with fictional values, a fictional ENSDF-style fixture, and deterministic synthetic spectra generated at runtime.

It does not include:

- raw or reduced experimental event files;
- ROOT files, spectra, detector matrices, or collaboration workbooks;
- unpublished level schemes, gates, calibration nodes, or lifetime results;
- authentication tokens, SSH keys, passwords, hostnames, or access instructions;
- personal directories or machine-specific absolute paths;
- proprietary runtime bundles or generated internal reports;
- third-party articles, figures, or database snapshots.

## Data classes

| Class | Examples | Repository policy |
|---|---|---|
| Public source code | Package, tests, schemas | Allowed under project license |
| Synthetic fixtures | Fictional levels, deterministic counts | Allowed when clearly labeled |
| Public upstream metadata | URLs, record IDs, citations | Allowed with provenance |
| Public upstream datasets | ENSDF/XUNDL records | Fetch at runtime; do not vendor by default |
| Collaboration data | Events, spectra, gates, internal tables | Excluded unless owners explicitly authorize release |
| Personal or security data | Keys, tokens, private paths | Always excluded |
| Third-party publications/assets | Papers, figures, tables | Link and cite; redistribute only with permission |

## Runtime retrieval

`anspec fetch-ensdf` is an explicit user action. It writes retrieved material to the chosen local directory and emits a manifest. A fetched file does not automatically become redistributable project content. Users must review provider terms, citation requirements, and the needs of reproducibility before archiving or sharing it.

## Real-data adapter rule

An adapter for private or experimental data should expose only a documented interface to the public package. Keep the adapter configuration, real paths, event selection, and output outside version control unless all relevant owners approve release.

Recommended local pattern:

```text
private-analysis/
  input/             # collaboration-controlled data
  local-config/      # paths, gates, calibrations
  output/            # generated results
  public-export/     # reviewed, deliberately exported metadata only
```

## Release checklist

Before publishing a branch, release, issue attachment, or example:

1. Run `python tools/public_surface_audit.py`.
2. Inspect every newly added binary or large file.
3. Confirm fixtures are synthetic or publicly redistributable.
4. Search for keys, tokens, hostnames, usernames, personal paths, and unpublished labels.
5. Confirm code and prose are original or compatibly licensed.
6. Confirm data owners and collaborators have approved any non-synthetic material.
7. Verify that README claims match the released code and tests.

Automated scanning reduces risk but cannot determine collaboration ownership or publication status. Human review remains required.
