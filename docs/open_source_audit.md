# Public-Release Audit

## Audit objective

The public project was assembled from an author-owned research workflow through selective clean reimplementation. The goal was to preserve reusable scientific logic while excluding experiment-specific, security-sensitive, redundant, generated, or legally uncertain material.

## Included

- General NNDC/ENSDF retrieval and provenance concepts.
- A documented ENSDF subset parser written for this repository.
- Source-local F-D-G cascade enumeration and deterministic ranking.
- Transparent count-statistics assessment.
- A structured agent-review and human-approval protocol.
- General four-region subtraction, iterative centroid, PRD covariance, and GCD equations.
- Fictional configurations, a fictional ENSDF-style record, and synthetic spectra.
- Tests and documentation created for the public interface.

## Excluded

- Real experimental events, histograms, spectra, workbooks, and presentations.
- Unpublished isotope candidates, gate choices, calibration nodes, and result tables.
- Collaboration-only review packages and internal status artifacts.
- SSH keys, tokens, credentials, server access material, and host details.
- Local runtime installations, caches, generated output, and duplicated scripts.
- Files without a clear right to redistribute, including upstream publications and database snapshots.

## Reimplementation boundary

No private repository history or generated experimental artifact is published. The public modules express general methods with new interfaces, deterministic identifiers, explicit statuses, English documentation, and synthetic test fixtures. Scientific equations and conventions are documented so reviewers can compare the implementation with their own validated methods.

The author states that the released code and prompts were independently authored by the maintainer with GPT assistance. Contributors remain responsible for the originality and licensing of future submissions.

## Automated checks

`tools/public_surface_audit.py` rejects common release hazards:

- private-key blocks and credential-like assignments;
- personal absolute home paths and a known internal path pattern;
- unresolved repository placeholders;
- selected binary/research file types; and
- public files larger than the configured limit.

CI also runs unit and end-to-end tests plus Ruff linting.

## Residual risks

Automated scans cannot determine whether a scientific idea is embargoed, whether every author has approved release, whether a method is physically valid for a detector, or whether a third-party phrase is substantially similar to protected text. Maintainer and collaborator review remain necessary before adding real-world material.

## Release verdict for version 0.1.0

The automated scan and manual selection review found no private experimental artifact, credential, personal path, or uncleared third-party dataset in the intended public surface. Version 0.1.0 contains general software, synthetic examples, and explicit limitations under Apache-2.0. This is a project-level engineering assessment, not legal advice or scientific validation.
