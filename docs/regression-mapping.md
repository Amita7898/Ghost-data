# Regression lineage and deliberate changes

No competition parser, data, expected answers, or transcripts were copied into
this repository. The existing engine informed the contracts and behavioral
regressions. The original remains separately preserved with its 86-test suite.

| Existing behavior | New coverage / change |
|---|---|
| Refusal, marketing opt-out, explicit deletion | Parameterized intent tests |
| Historical emails | Validity-aware identifiers, reassignment ambiguity |
| Audit cutoff | Future observation/capture/identity exclusion |
| Tombstones | Required field inventory + preserved stable reference |
| Retention | Explicit conditions; missing condition never defaults true |
| Verification | Independent rejection of fabricated or selectively cited proof |
| Replica presence | Positive subject-linked replica example |
| Dependency ordering | Prerequisite ordering, unresolved and cyclic plan blocking |
| Output stability | Deterministic report comparison and CLI integration |

Not all 86 original tests are portable: many assert competition-specific parsers,
operation names and CSV sequencing. Those remain preserved in the original
project; they are not falsely counted as new platform tests. Multilingual free
text and double negation are intentionally conservative rather than guessing.
The former verification-of-prior-deletion request shortcut is not treated as new
deletion authorization. Future audit requests need a separate explicit intent.
