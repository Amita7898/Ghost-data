# Evidence admission

| Timestamp | Meaning |
|---|---|
| `event_at` | Underlying operation; not proof of its result |
| `observed_at` | When the resource state was observed |
| `captured_at` | When its source was captured |
| `ingested_at` | When the investigation received it |
| `available_at` | Additional source availability restriction |
| `audit_at` | State reconstruction cutoff |
| `evidence_cutoff` | Optional stricter availability cutoff |

Events/observations must not follow `audit_at`. Capture, ingestion and explicit
availability must not follow `evidence_cutoff` (default `audit_at`). Equality is
admitted; chronology must be coherent. Current proof requires a subject-attributed
READBACK exactly at the audit cutoff. Earlier observations have no implied continuity.

Missing ingestion time is not replaced with capture time. For backward-compatible
source-only audits it is not required by default; when supplied it is always checked.
Set `request.require_ingestion_time=true` to require a receipt. Missing required or
late ingestion makes the observation ineligible. Typed aware timestamps reject naive,
malformed or contradictory legacy/explicit metadata. Equivalent differently encoded
legacy/explicit timestamps are conservatively rejected if their raw values conflict.

The canonical admission predicate checks time, resource and subject for policy,
independent proof, tools, and LLM proposals. A model cannot waive it or register a
new evidence item. Eligibility is rechecked for advisory follow-up citations, including
stale-cache cases. Source authenticity is still an explicit assumption.

Historically, all 18 unsupported verified conclusions in the pre-hardening 512-case
suite came from late ingestion. Fixed seeds after admission hardening had none.
The old reports remain recoverable from `v0.4.0`; [evaluation](evaluation.md) distinguishes
historical measurements from the current rerun. No private competition truth is used.
