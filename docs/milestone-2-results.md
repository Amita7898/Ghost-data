# Milestone 2 results

109 tests passed locally (53 core tests plus 56 generator/benchmark tests). The auditing kernel source is byte-identical to Milestone 1; its hashes are recorded separately. CI is configured, but no remote CI or GitHub publication occurred.

| Suite | Seed | Cases | Conclusion accuracy | Unsupported verified | False noncompliant |
|---|---:|---:|---:|---:|---:|
| small | 42 | 32 | 93.7500% | 1 | 0 |
| medium | 2026 | 128 | 93.7500% | 4 | 0 |
| large | 91827 | 512 | 92.9688% | 18 | 0 |

All suites ran three times per case with identical predictions and zero runtime errors. Total: 672 scenarios, 2,016 predictions. Inputs regenerate byte-for-byte from seed and version. Latencies are measured locally and include cold import time on the first prediction of the first suite.

## Large-suite safety and coverage

- authorization_accuracy: 0.96484375
- unsafe_refusals: 0
- evidence_attribution: 0.9831144465290806
- verification_covered: 882
- verification_supported: 882
- policy_violations: 18
- timestamp_violations: 18
- world_state_accuracy_when_decisive: 1.0
- world_decisive: 201
- world_state_decision_rate: 0.392578125
- median_ms: 0.1435834997209895
- p95_ms: 0.16645899995637592

Verification coverage is 100% of the 882 provable obligations, but 18 additional unsupported verification claims exist. Coverage alone is therefore not a safety score. World-state accuracy among decisive outputs is 100%, while the decision rate is only 39.26%; knowing a world happens to be compliant does not justify an unsupported proof claim.

## Failures and next steps

1. Late ingestion: 18/512 cases incorrectly return VERIFIED_WITHIN_SCOPE under the explicit benchmark availability contract. Ingestion time is currently an unvalidated observation field, so both kernel and checker miss it. Add a first-class availability timestamp and independently enforce it before LLM integration.
2. German refusal: 18/512 cases return INCONCLUSIVE instead of NOT_APPLICABLE. They do not authorize deletion or propose actions. Extend intent interpretation conservatively; benchmark precision and safety separately.
3. No source-authentication, OCR, PDF, open-ended language or live-system discovery capability is established by these tests. The generated cases use controlled JSON templates; increasing case count is not independent out-of-distribution evidence.

Full per-family and per-conclusion results, scenario IDs, raw predictions, citations, timings and failures are in benchmarks/results-*/results.json and report.md.

No runtime model calls were made: 0 tokens and $0 API cost. Future extraction/agent/challenger modes are explicit unimplemented adapter slots, not simulated agents. The final target remains the real LLM + FastAPI + React application. Milestone 3 has not begun.

## Data separation

The generator and oracle import no kernel modules. The runtime adapter takes only auditor-visible bytes and receives no world, labels, family names, or file paths. Expected answers are read after inference. Tests demonstrate that modifying labels cannot affect predictions. This is a verified application API boundary, not an OS filesystem sandbox; stronger deployment isolation is documented for future untrusted tools.
