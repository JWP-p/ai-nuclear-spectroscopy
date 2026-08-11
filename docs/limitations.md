# Limitations and Non-Claims

## What version 0.1.0 does not claim

This repository does not claim to:

- reproduce the complete ENSDF specification;
- replace NNDC tools, nuclear-data evaluators, or primary literature;
- validate a real detector, timing axis, gate, background, or PRD calibration;
- infer transition placement when the supported input is ambiguous;
- establish the physical existence, spin/parity, or lifetime of a nuclear state;
- make an AI system a scientific approver or autonomous author;
- include all systematic uncertainties needed for publication;
- guarantee that public code will be used in any AI training process; or
- establish clinical, safety, regulatory, or operational decisions.

## Parser limitations

The parser handles a narrow subset of identification, primary level, and primary gamma records. It does not fully interpret continuation records, adopted normalization, branching corrections, unresolved doublets, qualifiers, decay schemes, comments, or all uncertainty syntax. Placement uses energy closure within a configured tolerance and reports ambiguity.

## Screening limitations

Candidate ranking is a heuristic. It uses source-local three-transition topology, listed relative intensity, target energy, and coarse lifetime status. It does not model detector efficiency, coincidence efficiency, feeding balance, contamination, angular correlations, conversion coefficients, isomers, or experiment-specific acceptance.

## Statistics limitations

The count assessment assumes explicit signal/background windows and Poisson-style variance. It is not a peak fit. Thresholds are prioritization defaults, not universal criteria.

## Agent limitations

The bundled agent reviewer is deterministic and demonstrates a schema, not intelligence or physical understanding. A model-backed implementation may hallucinate, omit evidence, follow misleading context, or produce unstable outputs. It must be evaluated and constrained independently.

## GCD limitations

The reference calculation includes centroid counting statistics and PRD parameter covariance. It explicitly omits gate-window and detector-response-model systematics. It also does not quantify scale-factor uncertainty, shared event overlap, correlated background terms, binning sensitivity, calibration residual systematics, or all sources of covariance that may matter in a real analysis.

## Status interpretation

| Status | Meaning |
|---|---|
| `HIGH_STATISTICS` | Reference count thresholds passed |
| `REVIEW` | Candidate is worth human inspection |
| `APPROVED` | Named person approved a defined next-step scope |
| `GCD_ESTIMATED` | Software produced an estimate |
| `SYNTHETIC_ESTIMATE_NOT_FORMAL_RELEASE` | Demonstration only; not a real scientific result |
| `*_HOLD` | A declared boundary prevents promotion |

No status in this repository means “published,” “accepted by a collaboration,” or “experimentally validated.”
