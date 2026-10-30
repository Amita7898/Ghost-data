# Synthetic benchmark results

Mode: deterministic; seed: 42; repeated runs: 2.

Metrics describe generated scenarios, not real-world accuracy or LLM performance.

| Metric | Value |
|---|---|
| cases | 32 |
| runtime_error_cases | 0 |
| conclusion_accuracy | 1.0 |
| unsupported_verified | 0 |
| incorrect_noncompliant | 0 |
| authorization_accuracy | 1.0 |
| unsafe_refusals | 0 |
| evidence_attribution | 1.0 |
| valid_citations | 67 |
| citations | 67 |
| verification_coverage | 1.0 |
| verification_covered | 57 |
| verification_supported | 57 |
| policy_violations | 0 |
| timestamp_violations | 0 |
| world_state_accuracy_when_decisive | 1.0 |
| world_decisive | 12 |
| world_state_decision_rate | 0.375 |
| repeated_outputs_identical | True |
| median_ms | 0.5428745000699564 |
| p95_ms | 0.6982499999139691 |
| total_runtime_seconds | 0.15741133499841453 |

## By expected conclusion

| Category | Cases | Conclusion accuracy | Unsupported verified |
|---|---:|---:|---:|
| INCONCLUSIVE | 16 | 1.000 | 0 |
| NON_COMPLIANT | 5 | 1.000 | 0 |
| NOT_APPLICABLE | 4 | 1.000 | 0 |
| VERIFIED_WITHIN_SCOPE | 7 | 1.000 | 0 |

## By scenario family

| Category | Cases | Conclusion accuracy | Unsupported verified |
|---|---:|---:|---:|
| ambiguous_owner | 1 | 1.000 | 0 |
| ambiguous_request | 1 | 1.000 | 0 |
| anonymization_unknown | 1 | 1.000 | 0 |
| backup_blocked | 1 | 1.000 | 0 |
| backup_unblocked | 1 | 1.000 | 0 |
| conflicting_readbacks | 1 | 1.000 | 0 |
| deleted | 2 | 1.000 | 0 |
| failed_operation | 1 | 1.000 | 0 |
| future_evidence | 1 | 1.000 | 0 |
| historical_email | 1 | 1.000 | 0 |
| historical_phone | 1 | 1.000 | 0 |
| incorrect_identity | 1 | 1.000 | 0 |
| late_ingestion | 1 | 1.000 | 0 |
| marketing_optout | 1 | 1.000 | 0 |
| misleading_success | 2 | 1.000 | 0 |
| missing_evidence | 2 | 1.000 | 0 |
| partial_snapshot | 1 | 1.000 | 0 |
| prompt_injection | 1 | 1.000 | 0 |
| refusal_de | 1 | 1.000 | 0 |
| refusal_es | 1 | 1.000 | 0 |
| refusal_fr | 1 | 1.000 | 0 |
| remaining_replica | 2 | 1.000 | 0 |
| retention_active | 1 | 1.000 | 0 |
| retention_unknown | 1 | 1.000 | 0 |
| search_remaining | 1 | 1.000 | 0 |
| shared_resource | 1 | 1.000 | 0 |
| tombstone_missing_fields | 1 | 1.000 | 0 |
| tombstone_redacted | 1 | 1.000 | 0 |

## Failures

| Scenario | Family | Expected | Actual |
|---|---|---|---|

Evidence attribution counts cited IDs that are valid for the same subject/resource and eligible timestamps. Verification coverage counts correctly satisfied, provable obligations, not all real-world resources. World-state accuracy is selective: inconclusive and not-applicable outputs abstain. Timing is local wall-clock inference time; JSON reports retain each measurement. No runtime model calls were made in deterministic mode.
