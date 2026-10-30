# Synthetic benchmark results

Mode: deterministic; seed: 91827; repeated runs: 3.

Metrics describe generated scenarios, not real-world accuracy or LLM performance.

| Metric | Value |
|---|---|
| cases | 512 |
| runtime_error_cases | 0 |
| conclusion_accuracy | 1.0 |
| unsupported_verified | 0 |
| incorrect_noncompliant | 0 |
| authorization_accuracy | 1.0 |
| unsafe_refusals | 0 |
| evidence_attribution | 1.0 |
| valid_citations | 1048 |
| citations | 1048 |
| verification_coverage | 1.0 |
| verification_covered | 882 |
| verification_supported | 882 |
| policy_violations | 0 |
| timestamp_violations | 0 |
| world_state_accuracy_when_decisive | 1.0 |
| world_decisive | 183 |
| world_state_decision_rate | 0.357421875 |
| repeated_outputs_identical | True |
| median_ms | 0.3280414999835557 |
| p95_ms | 0.3909590000148455 |
| total_runtime_seconds | 0.4588587519978091 |

## By expected conclusion

| Category | Cases | Conclusion accuracy | Unsupported verified |
|---|---:|---:|---:|
| INCONCLUSIVE | 257 | 1.000 | 0 |
| NON_COMPLIANT | 73 | 1.000 | 0 |
| NOT_APPLICABLE | 72 | 1.000 | 0 |
| VERIFIED_WITHIN_SCOPE | 110 | 1.000 | 0 |

## By scenario family

| Category | Cases | Conclusion accuracy | Unsupported verified |
|---|---:|---:|---:|
| ambiguous_owner | 18 | 1.000 | 0 |
| ambiguous_request | 18 | 1.000 | 0 |
| anonymization_unknown | 18 | 1.000 | 0 |
| backup_blocked | 18 | 1.000 | 0 |
| backup_unblocked | 18 | 1.000 | 0 |
| conflicting_readbacks | 19 | 1.000 | 0 |
| deleted | 19 | 1.000 | 0 |
| failed_operation | 18 | 1.000 | 0 |
| future_evidence | 19 | 1.000 | 0 |
| historical_email | 18 | 1.000 | 0 |
| historical_phone | 18 | 1.000 | 0 |
| incorrect_identity | 18 | 1.000 | 0 |
| late_ingestion | 18 | 1.000 | 0 |
| marketing_optout | 18 | 1.000 | 0 |
| misleading_success | 19 | 1.000 | 0 |
| missing_evidence | 19 | 1.000 | 0 |
| partial_snapshot | 19 | 1.000 | 0 |
| prompt_injection | 18 | 1.000 | 0 |
| refusal_de | 18 | 1.000 | 0 |
| refusal_es | 18 | 1.000 | 0 |
| refusal_fr | 18 | 1.000 | 0 |
| remaining_replica | 19 | 1.000 | 0 |
| retention_active | 19 | 1.000 | 0 |
| retention_unknown | 18 | 1.000 | 0 |
| search_remaining | 18 | 1.000 | 0 |
| shared_resource | 18 | 1.000 | 0 |
| tombstone_missing_fields | 18 | 1.000 | 0 |
| tombstone_redacted | 18 | 1.000 | 0 |

## Failures

| Scenario | Family | Expected | Actual |
|---|---|---|---|

Evidence attribution counts cited IDs that are valid for the same subject/resource and eligible timestamps. Verification coverage counts correctly satisfied, provable obligations, not all real-world resources. World-state accuracy is selective: inconclusive and not-applicable outputs abstain. Timing is local wall-clock inference time; JSON reports retain each measurement. No runtime model calls were made in deterministic mode.
