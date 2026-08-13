# Project Governance

AI Nuclear Spectroscopy is a public research-software project. Its governance
keeps software collaboration open while preserving an explicit boundary around
physical interpretation, restricted data, and formal scientific claims.

## Roles

### Primary maintainer

`PanDa` (`@JWP-p`) is the project creator and primary maintainer. The primary
maintainer is responsible for the public roadmap, release decisions, repository
security settings, and the final decision on changes that affect the project's
scientific contracts.

### Core maintainers

Core maintainers are trusted contributors who take continuing responsibility for
one or more public areas of the project. A core maintainer normally:

- reviews pull requests in an assigned area;
- keeps tests and documentation aligned with the implementation;
- helps triage issues and shape the roadmap; and
- documents disagreements, assumptions, and unresolved scientific risk.

Core-maintainer status is granted by the primary maintainer after a contributor
has accepted repository access and demonstrated sustained, reviewable work. It
is a governance role, not a claim of authorship or scientific authority.

### Contributors and reviewers

Contributors may propose code, tests, documentation, prompts, schemas, or
public-data adapters through pull requests. Domain reviewers are invited when a
change affects nuclear-data interpretation, detector conventions, timing signs,
background subtraction, PRD calibration, uncertainty propagation, or scientific
status promotion. A reviewer can advise without becoming a repository
maintainer.

## Decision boundaries

The project uses the following default review boundaries:

| Change | Minimum review expectation |
| --- | --- |
| Documentation, examples, or tests with no contract change | One maintainer review and passing CI |
| Public API, schema, prompt contract, or data-model change | Maintainer review, tests, and an updated changelog entry |
| Physics convention, timing sign, gate definition, PRD, or uncertainty change | Maintainer review plus review by someone competent in the affected method |
| Scientific status promotion or formal experimental release | Explicit qualified-human approval outside automated CI |
| New data, figures, or adapters derived from collaboration material | Ownership and redistribution review before publication |

No model output, passing test, or maintainer approval can replace the qualified
human review required for a formal scientific claim.

## Working agreement

1. Prefer a focused pull request over direct edits to `main`.
2. Keep source identity, units, conventions, evidence, counterevidence, and
   uncertainty scope visible.
3. Mark synthetic fixtures and illustrative values unambiguously.
4. Never publish credentials, private paths, restricted data, or unpublished
   collaboration material.
5. Explain what was checked and what remains uncertain in the pull request.

The repository's `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and
`docs/data_governance.md` provide the operational details for these principles.

## Changes to governance

Governance changes should be proposed as pull requests and recorded in the
changelog when they alter contributor responsibilities, review boundaries, or
release authority. The primary maintainer may make an emergency security change
and should document it afterward.
