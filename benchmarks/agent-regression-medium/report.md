# Synthetic benchmark results

Mode: deterministic; seed: 2026; repeated runs: 2.

Metrics describe generated scenarios, not real-world accuracy or LLM performance.

| Metric | Value |
|---|---|
| cases | 128 |
| runtime_error_cases | 0 |
| conclusion_accuracy | 1.0 |
| unsupported_verified | 0 |
| incorrect_noncompliant | 0 |
| authorization_accuracy | 1.0 |
| unsafe_refusals | 0 |
| evidence_attribution | 1.0 |
| valid_citations | 270 |
| citations | 270 |
| verification_coverage | 1.0 |
| verification_covered | 228 |
| verification_supported | 228 |
| policy_violations | 0 |
| timestamp_violations | 0 |
| world_state_accuracy_when_decisive | 1.0 |
| world_decisive | 48 |
| world_state_decision_rate | 0.375 |
| repeated_outputs_identical | True |
| median_ms | 0.5636664998291963 |
| p95_ms | 0.7086250002430461 |
| total_runtime_seconds | 0.1352744670039101 |

## By expected conclusion

| Category | Cases | Conclusion accuracy | Unsupported verified |
|---|---:|---:|---:|
| INCONCLUSIVE | 64 | 1.000 | 0 |
| NON_COMPLIANT | 18 | 1.000 | 0 |
| NOT_APPLICABLE | 16 | 1.000 | 0 |
| VERIFIED_WITHIN_SCOPE | 30 | 1.000 | 0 |

## By scenario family

| Category | Cases | Conclusion accuracy | Unsupported verified |
|---|---:|---:|---:|
| ambiguous_owner | 5 | 1.000 | 0 |
| ambiguous_request | 4 | 1.000 | 0 |
| anonymization_unknown | 4 | 1.000 | 0 |
| backup_blocked | 5 | 1.000 | 0 |
| backup_unblocked | 5 | 1.000 | 0 |
| conflicting_readbacks | 5 | 1.000 | 0 |
| deleted | 5 | 1.000 | 0 |
| failed_operation | 4 | 1.000 | 0 |
| future_evidence | 5 | 1.000 | 0 |
| historical_email | 5 | 1.000 | 0 |
| historical_phone | 5 | 1.000 | 0 |
| incorrect_identity | 4 | 1.000 | 0 |
| late_ingestion | 4 | 1.000 | 0 |
| marketing_optout | 4 | 1.000 | 0 |
| misleading_success | 5 | 1.000 | 0 |
| missing_evidence | 5 | 1.000 | 0 |
| partial_snapshot | 5 | 1.000 | 0 |
| prompt_injection | 4 | 1.000 | 0 |
| refusal_de | 4 | 1.000 | 0 |
| refusal_es | 4 | 1.000 | 0 |
| refusal_fr | 4 | 1.000 | 0 |
| remaining_replica | 5 | 1.000 | 0 |
| retention_active | 5 | 1.000 | 0 |
| retention_unknown | 5 | 1.000 | 0 |
| search_remaining | 4 | 1.000 | 0 |
| shared_resource | 4 | 1.000 | 0 |
| tombstone_missing_fields | 5 | 1.000 | 0 |
| tombstone_redacted | 5 | 1.000 | 0 |

## Failures

| Scenario | Family | Expected | Actual |
|---|---|---|---|

Evidence attribution counts cited IDs that are valid for the same subject/resource and eligible timestamps. Verification coverage counts correctly satisfied, provable obligations, not all real-world resources. World-state accuracy is selective: inconclusive and not-applicable outputs abstain. Timing is local wall-clock inference time; JSON reports retain each measurement. No runtime model calls were made in deterministic mode.
