"""Bounded JSON ingestion, content hashes and source locators; no SQL execution."""

import hashlib
import json
from pathlib import Path

from .identity import resolve
from .models import Bundle

MAX_BUNDLE_BYTES = 5_000_000


def load(path):
    """Read bounded artifact bytes and delegate to the common ingestion boundary."""
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_BUNDLE_BYTES + 1)
    return load_bytes(raw)


def load_bytes(raw: bytes) -> tuple[Bundle, str]:
    """Validate original JSON bytes without creating temporary evidence files."""
    if len(raw) > MAX_BUNDLE_BYTES:
        raise ValueError("evidence bundle exceeds 5 MB limit")

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    data = json.loads(raw, object_pairs_hook=pairs)
    return Bundle.model_validate(data), hashlib.sha256(raw).hexdigest()


def admission_reasons(bundle, observation, target, subject):
    """Canonical admission gate for observations and proposed proof citations."""
    o = observation
    cutoff = bundle.request.audit_at
    reasons = []
    if o.key != target.key:
        reasons.append("resource_mismatch")
    for name in (
        "event_at",
        "observed_at",
        "captured_at",
        "ingested_at",
        "available_at",
    ):
        at = getattr(o, name)
        limit = (
            cutoff
            if name in ("event_at", "observed_at")
            else (bundle.request.evidence_cutoff or cutoff)
        )
        if at is not None and at > limit:
            reasons.append(name + "_after_cutoff")
    if bundle.request.require_ingestion_time and o.ingested_at is None:
        reasons.append("ingestion_time_missing")
    if o.event_at and o.event_at > o.observed_at:
        reasons.append("event_after_observation")
    if o.captured_at < o.observed_at:
        reasons.append("capture_before_observation")
    if o.ingested_at and o.ingested_at < o.captured_at:
        reasons.append("ingestion_before_capture")
    if resolve(o.identifier, o.observed_at, cutoff, bundle.identities) != {subject}:
        reasons.append("subject_unresolved")
    return tuple(reasons)


def eligible(bundle, target, subject):
    return [
        o
        for o in bundle.observations
        if not admission_reasons(bundle, o, target, subject)
    ]


def provenance(bundle, digest):
    result = {
        o.id: f"sha256:{digest}#/observations/{n}"
        for n, o in enumerate(bundle.observations)
    }
    for section in ("identities", "targets", "rules"):
        for n, _ in enumerate(getattr(bundle, section)):
            result[f"{section}:{n}"] = f"sha256:{digest}#/{section}/{n}"
    return result
