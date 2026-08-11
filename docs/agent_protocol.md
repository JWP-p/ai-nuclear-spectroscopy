# Scientific-Agent Protocol

## Objective

The agent layer helps a researcher organize evidence and decide what to inspect next. It must not conceal uncertainty behind fluent prose or promote its own recommendation into a scientific conclusion.

## Input contract

An agent reviewing a candidate should receive:

- exact candidate and source identifiers;
- nuclide, target level, and F-D-G transition identities;
- gate orientation and physical convention;
- parsed lifetime and placement status;
- experimental-statistics assessment for every required transition;
- provenance manifest or source references;
- known limitations and conflicts; and
- the allowed decision scope.

Missing evidence must be represented as missing, not reconstructed from model memory.

## Output contract

Each review contains:

```json
{
  "candidate_id": "CASCADE_...",
  "claim": "...",
  "supporting_evidence": ["..."],
  "counterevidence": ["..."],
  "recommendation": "REVIEW | HOLD | REJECT",
  "confidence": "LOW | MEDIUM | HIGH",
  "required_next_action": "..."
}
```

The complete prompt schema is in `prompts/schemas/candidate_review.schema.json`.

## Evidence discipline

The agent should:

1. cite structured fields or attached artifacts for every material claim;
2. separate direct observations from calculations and interpretations;
3. name missing evidence and plausible failure modes;
4. prefer a hold over inventing a transition, gate, count, calibration, or citation;
5. avoid requests for hidden chain-of-thought; and
6. provide a concise rationale that a human can audit.

## Human authority boundary

An agent may prioritize, compare, flag, summarize, or propose a next test. It may not:

- certify source data;
- authorize access or release of collaboration data;
- approve experimental gates or timing conventions;
- convert a diagnostic estimate into a formal result;
- assign authorship or publication readiness; or
- suppress contradictory evidence.

The workflow records human approval as a separate object with a candidate, reviewer, scope, and timestamp. Model text cannot satisfy that requirement.

## Reproducibility

For provider-backed agents, record model name, provider, version/date where available, generation parameters, prompt version, tool permissions, retrieved sources, and output schema version. Do not store secrets or private model-provider metadata in public artifacts.

The bundled reviewer is deterministic and does not call a model. This makes the repository runnable offline and provides a stable reference against which model-backed implementations can be evaluated.

The synthetic workflow also records a three-round trace: `candidate_selector`, `evidence_critic`, and `review_synthesizer`. The trace preserves unresolved counterevidence and ends at `READY_FOR_HUMAN_DECISION`; it cannot generate approval. It demonstrates iterative reasoning structure, not an actual GPT call. Provider-backed implementations should use the prompt sequence in `prompts/` while preserving the same boundary.

## Evaluating an agent implementation

Useful evaluation questions include:

- Does it preserve candidate and source identity?
- Does it detect a missing required transition assessment?
- Does it expose low statistics and calibration extrapolation?
- Does it distinguish evidence from recommendation?
- Does it refuse promotion when human approval is absent?
- Does it produce valid schema without unsupported citations?
- Can a second reviewer reconstruct why it recommended a candidate?

Agreement with a preferred answer is not enough. The evidence path and failure behavior matter.
