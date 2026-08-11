# Provenance and Citation

## Why provenance is part of the result

A number without its source chain cannot be reliably reproduced. Nuclear-data evaluations change, datasets may contain multiple source types, and local analysis choices can alter candidate identity. This project therefore carries provenance inside its domain records and output manifests.

## Retrieval manifest

The NNDC client records:

- source database and endpoint;
- upstream `datasetcheck` identifiers;
- nuclide, dataset title, record identifier, and revision text;
- retrieval time in UTC;
- content type and byte count; and
- SHA-256 of the returned ENSDF text.

The manifest identifies what the software received. It does not certify that the upstream evaluation is correct or that the record is suitable for a particular experiment.

## Workflow manifest

The demonstration provenance manifest records input and configuration hashes, software version, generation time, and scientific status. The accompanying `workflow_result.json` retains source identifiers, stable candidate identifiers, approval scope, equations represented by the code, and omitted uncertainty components.

## Citation layers

A research output may need several distinct citations:

1. **Nuclear data:** the individual ENSDF evaluation, publication, or dated database version specified by NNDC guidance.
2. **Experimental data:** the experiment, facility, detector system, and collaboration source under the relevant policy.
3. **Method:** literature describing the applicable GCD/centroid and PRD methodology.
4. **Software:** this repository and any scientific dependencies used.
5. **AI system:** model/provider/version and interaction policy when materially relevant to reproducibility.

The repository's `CITATION.cff` covers only layer 4. It never substitutes for layers 1–3.

## Stable scientific identity

The parser and screening code intentionally avoid collapsing different evaluated sources into one canonical transition. Stable IDs are hashes over source-local fields; they are reproducible handles within this implementation, not universal NNDC identifiers.

If two sources disagree, preserve both records and make the conflict explicit. Reconciliation is a scientific decision that belongs in a documented review layer.

## Recommended archival practice

For a formal analysis package, archive:

- the exact authorized input or durable public identifier;
- retrieval and workflow manifests;
- configuration and software commit hash;
- environment or dependency lock information;
- selected candidate and gate definitions;
- calibration inputs and covariance;
- systematic-variation results;
- reviewer approvals and scope; and
- citations for every upstream source.

Do not place restricted data in a public archival bundle merely to improve reproducibility. Use controlled-access archives when required.

## Official references

Provider and citation links are collected in [references.md](references.md). Always consult the current upstream guidance at the time of research use.
