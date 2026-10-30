# Synthetic world generation and benchmarking (Milestone 2)

This benchmark is a foundation for the planned real LLM agent and React/FastAPI
application. No model or frontend is implemented in this milestone.

## Reproduce

From the repository root, in the installed project virtual environment:

```sh
python -m ghost_data_bench.generate /tmp/ghost-suite --seed 42 --size small
python -m ghost_data_bench.run /tmp/ghost-suite --output /tmp/ghost-results --repeats 3
pytest -q
```

Use a fresh destination each time: generation and report commands refuse to
replace an existing directory. `small`, `medium`, and `large` mean 32, 128, and
512 cases. `--count N` overrides the size, with an upper bound of 10,000. Seeds
are integers. Same seed/count/version produces byte-identical suite files.
Scenario families cycle evenly; this is a stratified suite, not a prevalence
estimate. Counts below 28 do not cover every family. Seed changes identifiers,
identity history timestamps, and audit dates, not just file names.

The representative 32-case seed-42 suite is included under
`benchmarks/representative/`. Medium seed 2026 and large seed 91827 suites can be
regenerated using the same commands with the corresponding size and seed.
Results from all three runs are retained under `benchmarks/results-*`.

## Layers

1. `world.py:generate_world` constructs simulated people, historical email and
   phone mappings, resource ownership, policy treatments, actual resource states,
   and operation outcomes. It does not invoke the kernel.
2. `world.py:project` builds observations, incomplete/misleading claims, temporal
   metadata and visible policies. Future PDF/log/image renderers can implement
   this projection boundary; none are currently implemented.
3. `oracle.py` independently adjudicates evidence-supported conclusions and
   actual world state. It imports no kernel implementation. Hand-checked contract
   tests cover expected scenario outcomes, and scorer mutation tests check unsafe
   predictions. This reference is still software and can contain bugs; it is not
   formal proof or an independent human audit.
4. `generate.py` writes `visible/<opaque-id>.json` and separate
   `evaluator_only/<opaque-id>.json`. Expected results, family names, seed metadata,
   true ownership and real operation success are evaluator-only. The manifest
   records input hashes and reproduction parameters.
5. `adapters.py` passes only visible JSON bytes to the kernel. No suite directory,
   expected answers, world objects, or family name is part of its runtime contract.
6. `run.py` loads expected results after prediction and `score.py` scores them.

The auditor cannot conclude deletion merely because the generator knows it
succeeded. Missing evidence produces INCONCLUSIVE even in a compliant world.
A false success claim may coexist with a remaining resource, but without a valid
readback the correct evidence conclusion is still INCONCLUSIVE.

## Isolation boundary

Tests verify that kernel modules do not import benchmark modules, runtime inputs
have only the allowlisted bundle schema, labels can be changed without changing
predictions, and modified visible files fail integrity checks. The kernel is a
pure callable with no filesystem tools; it receives only visible bytes/models.

This is application-level data isolation, **not an operating-system sandbox**.
A malicious adapter with arbitrary Python/filesystem execution could read the
suite directory. Future LLM tools must expose only registered visible artifacts;
never grant arbitrary filesystem/shell access or index the repository. For a
stronger hostile-code boundary, run inference in a separate container mounting
only `visible/`, then score exported predictions outside that container. The
benchmark does not claim that this deployment isolation already exists.

Evaluator-only files are independent fictional test truth and may be published
as benchmark assets, but must never be mounted in runtime evidence tools or used
as prompt examples. Never publish competition truth, private evidence, or chats.

## Metric definitions

- Conclusion accuracy: exact evidence-supported conclusion matches / cases.
- Per-category accuracy: same measure grouped by expected conclusion and family.
- Unsupported verified: predictions claiming VERIFIED_WITHIN_SCOPE where the
  evidence oracle does not support it, even if the real world is compliant.
- Incorrect noncompliant: predictions of NON_COMPLIANT without oracle support.
- Evidence attribution: citations valid for the subject/resource and temporal
  eligibility / all emitted citations. This includes availability eligibility;
  it is broader than identity matching alone. Zero citations yields null, not 1.
- Verification coverage: correctly satisfied provable obligations / all
  oracle-satisfied obligations. This does not measure inventory discovery or
  prove unsupported obligations. Read with unsupported-verification counts.
- Authorization accuracy: exact intent category match. Safe refusal handling is
  separate: returning ambiguous without action is safe but not fully accurate.
- Policy violations: decisive obligation assessments inconsistent with the oracle.
- Timestamp violations: cited observations with future event/observation/capture
  or ingestion availability as applicable (scorer checks observation, capture,
  ingestion; event_at is contextual only and not a separate proof timestamp).
- World-state accuracy: comparison only for decisive predictions; abstention rate
  is reported. It must not be confused with evidence-supported accuracy.
- Runtime: perf_counter around adapter prediction, excluding file loading and
  scoring; the first call includes lazy module imports. Reports include median,
  nearest-rank p95, total time across repetitions, and individual measurements.
  Latency is machine dependent and is not expected to reproduce byte-for-byte.

## Availability contract and uncovered weakness

For these synthetic suites an observation must have been observed, captured,
and ingested by audit_at. Ingestion is represented in `fields.ingested_at` until
it becomes a first-class domain field. The Milestone 1 kernel checks observation
and capture timestamps but not ingestion. The late-ingestion scenario therefore
produces an unsupported verified conclusion. This is an explicit new contract
probe, not a claim that the original competition required ingestion semantics.

German refusal is safely ambiguous in the current limited-language grammar, but
incorrect against the intended NOT_APPLICABLE label. No kernel correction was
made to hide these failures.

## Scope and limitations

The 28 families are controlled structured probes, not naturalistic production
coverage. Each has three scoped resources and decoys. Parameters vary by seed,
but templates are shared between suite sizes; larger scores are not independent
out-of-distribution validation. Shared-resource/ambiguous-ownership scenarios test
safe abstention, not collaborative identity disambiguation. Prompt injection is
business text in an observation; passing this test with a non-LLM kernel says
nothing about a future model's resistance. Source authenticity is assumed at the
adapter boundary; arbitrary forged READBACKs remain outside the current trust
model. No PDF/OCR parsing, fuzzing or real connector throughput is benchmarked.

## Milestone 3 comparison interface

`RuntimeAdapter.predict(visible_bytes) -> report` supports registered adapters.
Mode names are `deterministic`, `extraction`, `agent`, and `agent_challenger`.
Only deterministic is implemented; others fail explicitly rather than simulate
agent results. Future adapters must emit the same assessment/provenance contract,
real usage data, and readable traces. Run identical visible suites with disjoint
labels, repeat stochastic agents, then compare safety, grounding, coverage,
latency and cost. Add held-out templates and perturbations before claiming LLM
improvement. Selective challenger behavior is a benchmark mode, not a mandate
for a multi-agent framework.
