# Generalized Centroid-Difference Method

## Scope

This document states the convention implemented by the synthetic reference workflow. Detector-specific analyses must verify axes, gates, subtraction scales, PRD calibration, and uncertainty assumptions against their own acquisition and analysis chain.

## Four-region timing subtraction

For each timing orientation, the workflow accepts four equally binned spectra:

- `peak`: both energy selections in their peak windows;
- `background_x`: x in background and y in peak;
- `background_y`: x in peak and y in background; and
- `background_xy`: both selections in background.

With scale factors `s_x`, `s_y`, and `s_xy`, the net signed spectrum is

\[
S_i=P_i-s_xB_{x,i}-s_yB_{y,i}+s_{xy}B_{xy,i}.
\]

Assuming independent Poisson counts, the reference statistical variance is

\[
V_i=P_i+s_x^2B_{x,i}+s_y^2B_{y,i}+s_{xy}^2B_{xy,i}.
\]

The implementation does not estimate uncertainty in the scale factors. Real analyses should add it where relevant.

## Signed iterative centroid

The centroid inside a selected time window is

\[
C=\frac{\sum_i t_i S_i}{\sum_i S_i}.
\]

Negative background-subtracted bins remain signed; they are not clipped before the centroid. The first centroid uses the complete supplied range. Subsequent estimates use a symmetric window of configurable half-width around the previous centroid.

Convergence occurs when the shift is smaller than the larger of the configured tolerance and the minimum positive bin spacing. If the iteration alternates between two centroids, the implementation returns their midpoint and adds half the cycle separation in quadrature to the larger statistical uncertainty. Non-convergence is recorded.

The reference uncertainty is

\[
\sigma_C^2=\frac{\sum_i V_i(t_i-C)^2}{\left|\sum_iS_i\right|^2}.
\]

This is a transparent counting-statistics approximation. It does not include window, binning, fit-model, time-walk, or detector-response systematics.

## Prompt-response-difference model

The implemented response curve is

\[
R(E)=\frac{a}{\sqrt{b+E}}+cE+d,
\]

with a declared energy calibration range. Only the difference enters the lifetime:

\[
\Delta R=R(E_D)-R(E_F).
\]

For parameter vector `p = (a, b, c)`, the covariance contribution is evaluated from

\[
\sigma_{\Delta R}^2=J\,\Sigma_p\,J^T,
\]

where `J` is the difference of the response gradients at decay and feeder energies. The constant `d` cancels from the difference and is therefore excluded from this covariance representation.

The helper that constructs a covariance matrix performs a weighted linearized normal-matrix inversion at supplied calibration points. A production calibration should also examine goodness of fit, residual structure, shared systematic components, and model adequacy.

## Lifetime convention

With Delay and Anti-delay centroids defined by the experiment's verified orientation,

\[
\Delta C=C_{delay}-C_{anti}.
\]

The mean life and half-life are

\[
\tau=\frac{\Delta C-\Delta R}{2},
\qquad
T_{1/2}=\ln(2)\tau.
\]

For independent centroid and PRD terms, the reference uncertainty is

\[
\sigma_\tau=\frac{1}{2}\sqrt{\sigma_{\Delta C}^2+\sigma_{\Delta R}^2}.
\]

## Hold conditions

The implementation records a hold when:

- the lifetime estimate is non-positive;
- either transition energy lies outside the PRD calibration range; or
- an upstream step has not received the required human approval.

Additional real-analysis hold conditions should include failed axis/orientation checks, inadequate peak statistics, unstable backgrounds, unresolved contaminants, poor calibration quality, or incomplete systematic studies.

## What the synthetic test proves

The deterministic fixture verifies that the implemented equations, stage boundary, serialization, and covariance path behave consistently. It does not validate the convention for a particular detector, the response function for a real calibration, or a nuclear-state lifetime.
