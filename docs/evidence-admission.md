# Evidence admission: Milestone 2.1

All 18 unsupported verified cases in the original seed-91827 large benchmark
were late_ingestion cases. IDs and original scoring details are preserved in
milestone-21-investigation.json. No other failure family contributed.

Temporal semantics:
- event_at: the underlying operation/event; not proof of resulting state.
- observed_at: when the represented resource state was actually observed.
- captured_at: when the source artifact/readback was captured.
- ingested_at: when the investigation received it; distinct from capture.
- available_at: any additional source-release/availability constraint.
- audit_at: the state reconstruction cutoff.
- evidence_cutoff: optional stricter availability cutoff, never after audit_at.

Events and observations must be no later than audit_at. Capture, ingestion and
explicit availability must be no later than evidence_cutoff (audit_at by default).
Equality is admitted. Supplied chronology must be coherent. For current proof,
READBACK observations must still be exactly at audit_at; earlier observations do
not silently establish continuity. Claims never become state proof.

Legacy fields.event_at and fields.ingested_at are parsed into typed aware-datetime
fields. Conflicting explicit and legacy values are rejected, as are naive or
malformed timestamps. Different timestamp strings for the same instant are
conservatively treated as conflicting when both encodings are supplied.

Missing ingestion time remains unknown; it is not replaced with capture time.
For backward compatibility the default rule audits source availability and does
not require an ingestion receipt when none is supplied. Any supplied receipt is
always enforced. Set request.require_ingestion_time=true to require an explicit
receipt; missing ingestion then makes evidence inadmissible. This distinction
supports source-only historical artifacts while allowing strict investigation
availability. No late supplied ingestion is waived by the compatibility rule.

Canonical admission_reasons in evidence.py checks timestamps, chronology, exact
system/resource identity and subject attribution. Both policy evaluation and the
independent verifier use this gate. The verifier independently rechecks state
proof and citation completeness; it does not trust policy assessments. Future
LLM proposals must resolve citations against the registered bundle and pass
check(bundle, report); model-supplied observations must undergo schema validation
and source registration, never enter as trusted proof directly.

German refusal patterns recognize supported negative forms without adding German
affirmative authorization. Unsupported wording and double negation remain
ambiguous. This is a conservative grammar, not general multilingual understanding.

Remaining limits: metadata/source authenticity is trusted at the adapter boundary;
unknown timestamps need investigation-specific requirements; old observations
have no continuity model; identity ambiguity remains unresolved. Tests cover
structured synthetic inputs, not unrestricted language or real connector security.
