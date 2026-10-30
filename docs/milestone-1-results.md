# Milestone 1 results

Local Python 3.12 verification: **53 pytest cases passed**. The original project
suite also passed **86 tests**; its source and submission artifacts compared
byte-for-byte equal to the preserved baseline after testing. These are different
suites, not 139 platform tests. No accuracy improvement or leaderboard score is
claimed. CI configuration is present; a remote GitHub run has not occurred.

Actual demonstration results:

- claim_only.json: INCONCLUSIVE
- partial_snapshot.json: INCONCLUSIVE
- remaining_replica.json: NON_COMPLIANT
- scoped_absence.json: VERIFIED_WITHIN_SCOPE

SQLite evidence/report/event round trip passed. Editable package installation and
CLI JSON output were tested. Repeated evaluation of identical input produced
identical reports. Run IDs and persistence timestamps intentionally vary.

Confirmed defects addressed in the new core:
- Explicit French/Spanish refusals cannot authorize deletion.
- Double negation remains unresolved instead of guessing authorization.
- Reassigned/historical identity ambiguity cannot silently select a subject.
- Row ownership never spreads from other rows in a document.
- Omitted redaction fields do not establish redaction.
- Unknown policy conditions do not implicitly permit deletion.
- Claims and incomplete snapshots cannot prove absence.
- Missing backup-presence evidence cannot establish safe retention/blocking.
- Independent validation rejects forged pass states and selective citations.
- Unresolved prerequisites and dependency cycles withhold remediation plans.

Runtime model calls: 0. Runtime input/output tokens: 0. Runtime API cost: $0.
Coding-assistant usage is separate and is not measured by this application.

No LLM agent, synthetic world benchmark, web API, frontend, or replay mode is
implemented yet. Milestones 2–5 remain subject to user approval. Licensing and
publication review remain outstanding. No GitHub repository was created or pushed.
