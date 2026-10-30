# Synthetic benchmark results

Mode: deterministic; seed: 91827; repeated runs: 3.

Metrics describe generated scenarios, not real-world accuracy or LLM performance.

| Metric | Value |
|---|---|
| cases | 512 |
| runtime_error_cases | 0 |
| conclusion_accuracy | 0.9296875 |
| unsupported_verified | 18 |
| incorrect_noncompliant | 0 |
| authorization_accuracy | 0.96484375 |
| unsafe_refusals | 0 |
| evidence_attribution | 0.9831144465290806 |
| valid_citations | 1048 |
| citations | 1066 |
| verification_coverage | 1.0 |
| verification_covered | 882 |
| verification_supported | 882 |
| policy_violations | 18 |
| timestamp_violations | 18 |
| world_state_accuracy_when_decisive | 1.0 |
| world_decisive | 201 |
| world_state_decision_rate | 0.392578125 |
| repeated_outputs_identical | True |
| median_ms | 0.1435834997209895 |
| p95_ms | 0.16645899995637592 |
| total_runtime_seconds | 0.212705605006704 |

## By expected conclusion

| Category | Cases | Conclusion accuracy | Unsupported verified |
|---|---:|---:|---:|
| INCONCLUSIVE | 257 | 0.930 | 18 |
| NON_COMPLIANT | 73 | 1.000 | 0 |
| NOT_APPLICABLE | 72 | 0.750 | 0 |
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
| late_ingestion | 18 | 0.000 | 18 |
| marketing_optout | 18 | 1.000 | 0 |
| misleading_success | 19 | 1.000 | 0 |
| missing_evidence | 19 | 1.000 | 0 |
| partial_snapshot | 19 | 1.000 | 0 |
| prompt_injection | 18 | 1.000 | 0 |
| refusal_de | 18 | 0.000 | 0 |
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
| 452beabca38c69c3 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 44065eedc18f6848 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 0d06c2d1d94731ee | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 5abb707cb7b5690b | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| c254a9542a4b7d69 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 795fb6ef75237d95 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 2c8039dc8d56f9f5 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 9629ccec71e29d67 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| d682206ac2fe71b5 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| f07b3d7b0a832c28 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 920ad5e903de4bc2 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 4a4dd2a69b8b4403 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 276a3e4e7694387f | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| dd73b49627e8bc32 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| beddab60caaced44 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| a652ce6424c7be87 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 8520676bc42f0bff | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 239cf99f866320b3 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 2ba32a3567afb8f5 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 9e9174a91f7b539f | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 3c6b27d5a933bb2d | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 5f09f9ea3a4cc3f7 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 940730dae026215c | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 140b7fdabfc01f94 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| fc6021660fcc64ab | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 091274a6c23025cf | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 125e905189f9bc15 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| f887e382074a01a4 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 5e4376f08da04f2e | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| d029b60dd03b8d76 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 8d01aff7fd2ffc55 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| 2fc962c24960fb3c | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 59db927bf39253f7 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| d4aef3a7394edd93 | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |
| 18beaa2a8cafa543 | refusal_de | NOT_APPLICABLE | INCONCLUSIVE |
| afdb7f3674ce81bc | late_ingestion | INCONCLUSIVE | VERIFIED_WITHIN_SCOPE |

Evidence attribution counts cited IDs that are valid for the same subject/resource and eligible timestamps. Verification coverage counts correctly satisfied, provable obligations, not all real-world resources. World-state accuracy is selective: inconclusive and not-applicable outputs abstain. Timing is local wall-clock inference time; JSON reports retain each measurement. No runtime model calls were made in deterministic mode.
