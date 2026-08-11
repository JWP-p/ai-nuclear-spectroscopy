# Scientific Workflow

## Purpose

This workflow is a reusable reasoning scaffold for identifying promising nuclear-state lifetime paths and carrying an approved path into a generalized centroid-difference analysis. It makes the chronology, inputs, outputs, and promotion conditions explicit.

## Stage 1 — Retrieve or supply nuclear data

Input can be an explicitly fetched public NNDC ENSDF/XUNDL record or a user-supplied record whose use is authorized. The retrieval client stores upstream identifiers and a dated hash manifest.

Required review:

- confirm the intended nuclide and dataset type;
- preserve the evaluator/source identity;
- cite the underlying evaluation or database snapshot; and
- do not treat a search response as a frozen scientific source unless it has been archived under appropriate terms.

Output: source text plus provenance metadata.

## Stage 2 — Parse without erasing ambiguity

The parser reads identification, level, and gamma records needed by the demonstration. It preserves raw level energy, source line, half-life text, and placement status. Energy-closure inference is limited by an explicit tolerance.

Output: source-aware levels and transitions.

Promotion condition: the required transitions are placed unambiguously within the documented subset.

## Stage 3 — Enumerate F-D-G candidates

For each valid three-transition path, the workflow represents:

- `F`: the feeder into the target level;
- `D`: the decay out of the target level; and
- `G`: a remote coincidence gate, either upstream of `F` or downstream of `D`.

Only paths within one source dataset are assembled. Pure E0 transitions are excluded from gamma-gating candidates. Each orientation receives a distinct deterministic identifier.

Output: ranked candidate records with target, transition energies, gate position, lifetime status, intensity score, physics score, and source identity.

Promotion condition: a candidate has a complete, source-local F-D-G definition. A rank is a triage aid, not experimental proof.

## Stage 4 — Assess experimental statistics

For every required transition, the reference implementation evaluates:

\[
N_{net} = N_{signal} - \alpha N_{background}
\]

and

\[
\sigma_{net} = \sqrt{N_{signal} + \alpha^2 N_{background}}.
\]

The significance is `N_net / sigma_net`. Thresholds label observations as high statistics, usable statistics, or low/inconclusive.

Output: transition-level and candidate-level count assessments.

Promotion condition: every required observation is present and the candidate meets an explicitly chosen statistical threshold. Real analyses should replace this simple check with validated fitting and background models.

## Stage 5 — Produce a structured agent review

The agent contract consumes the candidate definition and count assessment, then emits:

- a concise claim;
- supporting evidence;
- counterevidence and missing evidence;
- confidence;
- recommendation; and
- required next action.

The record is evidence for a review process, not evidence that a model is correct. The bundled implementation is deterministic so the contract can be tested offline.

Output: one review record per candidate.

Promotion condition: none. An AI recommendation alone cannot promote a candidate.

## Stage 6 — Record human approval

A qualified reviewer approves one candidate for one named scope. Approval must identify the candidate, reviewer, scope, timestamp, and status.

Examples of narrow scope:

- generate diagnostic spectra;
- evaluate a fixed set of gates;
- run a synthetic demonstration; or
- perform a detector-specific timing analysis under an approved protocol.

Approval to run analysis is not approval to publish a lifetime.

Output: explicit approval record.

Promotion condition: approval is present and its scope covers the next step.

## Stage 7 — Construct timing spectra

The reference demonstration synthesizes four regions for Delay and Anti-delay orientations:

- peak–peak;
- peak–background in the x direction;
- background–peak in the y direction; and
- background–background.

They are combined as:

\[
S_{net}=S_{peak}-s_xS_{bg,x}-s_yS_{bg,y}+s_{xy}S_{bg,xy}.
\]

The positive cross term restores the background component subtracted twice by the two single-background terms.

Output: signed net timing spectra with propagated counting variances.

Promotion condition: regions, scales, axes, and Delay/Anti orientation have been verified for the actual detector workflow.

## Stage 8 — Estimate centroids and PRD correction

Signed centroids are iterated inside a window centered on the preceding estimate. Convergence and two-cycle resolution are reported. The response model is:

\[
R(E)=\frac{a}{\sqrt{b+E}}+cE+d.
\]

The GCD relations are:

\[
\Delta C=C_{delay}-C_{anti},
\]

\[
\Delta R=R(E_{decay})-R(E_{feeder}),
\]

\[
\tau=\frac{\Delta C-\Delta R}{2}, \qquad T_{1/2}=\ln(2)\tau.
\]

PRD parameter covariance is propagated with the difference Jacobian. Extrapolation outside the calibration range creates a hold status.

Output: centroid records, PRD difference, mean life, half-life, uncertainties, calibration status, and named uncertainty scope.

## Stage 9 — Review before formal use

A formal scientific result requires work not represented by the synthetic demonstration:

- raw-event and histogram identity checks;
- detector and timing-axis validation;
- gate and background systematic variations;
- calibration quality and applicability review;
- alternative-condition or independent-method comparison where available;
- collaboration review and authorization; and
- correct citation of nuclear data, experimental data, software, and methods.

The public workflow ends with an auditable estimate. It does not silently cross the boundary into a publication claim.
