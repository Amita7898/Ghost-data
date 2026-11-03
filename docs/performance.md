# Performance and evidence: what was actually measured

These are historical local measurements, not a fresh broad model evaluation or a
production SLA. See retained milestone reports/raw JSON for precise runs and failures.

## Structured evidence regression

Milestone 2.1 corrected an evidence availability defect and explicit German refusal
handling. Fixed seeds 42/2026/91827, 32/128/512 cases, repeated three times: 100%
conclusion accuracy, zero unsupported VERIFIED_WITHIN_SCOPE and zero incorrect
NON_COMPLIANT conclusions in all three suites. Large-suite authorization accuracy
and verification coverage were 100% on this generated contract. Before hardening,
the 512 suite had 18 unsupported verified conclusions and 92.9688% accuracy.

Sources: milestone-21-comparison.json, milestone-21-investigation.json and
benchmarks/hardening-*/results.json. Independent fictional worlds and evidence-only
oracles are separate from runtime inputs. Runtime code receives only visible JSON;
expected labels are opened after inference. These are controlled, shared-template
regressions, not independent datasets or a certification of source authenticity.

## Narrow natural-language diagnostic

Milestone 3 used four independently authored readback-note cases: presence, absence,
conflict and injection. One run per mode/case, same visible inputs and independent
labels. Final serialized result:

| Mode | Conclusion accuracy | Median seconds | Model calls | Input / output tokens |
|---|---:|---:|---:|---:|
| Deterministic kernel | 25% | 0.0003 | 0 | 0 / 0 |
| Single extraction | 75% | 25.9286 | 4 | 1,642 / 362 |
| Dynamic investigation | 75% | 148.7462 | 20 | 33,435 / 2,072 |

Both model modes had zero unsupported verified and zero false noncompliant
conclusions here. Agent: 21 tool calls, two accepted/three rejected hypotheses.
The agent established receipt absence, which extraction missed; extraction correctly
identified the injection-case violation, while the agent abstained. Conflict caused
safe inconclusive results. Both modes had two accepted source checks out of two.
The reviewed receipt grammar could also be implemented by an ordinary parser.

The source contract intentionally rejects arbitrary prose; this experiment measures
bounded extraction/orchestration, not open-ended semantic correctness. Four cases,
one model/seed and related templates cannot establish general superiority,
robustness or statistical repeatability. Earlier failed/concurrent prototypes are
retained separately and are not pooled into the final result.

Raw measurements: benchmarks/local-agent-final-results/results.json and metrics.md;
reproduction commands in local-agent.md. Historical modes in the general benchmark
adapter are placeholders; actual model comparisons use ghost_data_bench.local_agent.

## Full-stack integration

Milestone 4 actual Chrome test: a live Qwen3.5 investigation completed in 162.439 s,
five model turns/five tools, 8,130 input + 443 output tokens and 27 persisted events.
A separate actual run cancelled in 4.651 s after one model call. Source:
web-live-validation.json. Offline replay displays those kinds of recorded events
without inference; accelerated playback is not a latency claim.

Measured hardware: Apple M3, 16 GiB unified memory; Ollama 0.40.13, Qwen3.5 9.7B
Q4_K_M, bounded 16,384 context. Failed requests can consume unreported compute;
Ollama counters include repeated context, not unique evidence tokens. Paid local
runtime API cost was $0. Electricity, hardware and coding-assistant costs were not
measured. No Milestone 5 inference-speed or accuracy improvement is claimed.

## Next experiments (not implemented)

Use held-out evidence templates, repeated runs, broader languages and perturbations;
measure safety precision and abstention alongside recall. Profile duplicate context,
cache immutable tool results, compare smaller tool-capable models on identical
held-out inputs, and evaluate early stopping. Any model/contract change must retain
the deterministic admission and independent proof checks. Do not add multi-agent
orchestration without a measured benefit.
