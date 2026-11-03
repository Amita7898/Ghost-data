"""Fixed-seed contract testing; the oracle is hand-defined, not policy.evaluate."""

import copy
import json
import random
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from ghost_data.engine import audit
from ghost_data.models import Assessment, Bundle
from ghost_data.verifier import check

BASE = json.loads(
    (Path(__file__).parents[1] / "examples/scoped_absence.json").read_text()
)


@pytest.mark.parametrize("seed", range(40))
def test_randomized_independent_policy_proof_contract(seed):
    rng = random.Random(seed)
    data = copy.deepcopy(BASE)
    action = rng.choice(["DELETE", "RETAIN", "REDACT", "ANONYMIZE", "DISABLE", "BLOCK"])
    rule = data["rules"][0]
    rule.update(action=action)
    if action in {"REDACT", "ANONYMIZE"}:
        rule["required_fields"] = ["email"]
    o = data["observations"][0]
    o.update(
        coverage="EXACT_RESOURCE",
        fields={"email": ""},
        unlinking_verified=True,
        archive_present=True,
    )
    o["state"] = {
        "DELETE": "ABSENT",
        "RETAIN": "PRESENT",
        "REDACT": "PRESENT",
        "ANONYMIZE": "PRESENT",
        "DISABLE": "DISABLED",
        "BLOCK": "BLOCKED",
    }[action]
    mechanism = rng.choice(
        ["valid", "missing", "conflict", "partial", "late", "ambiguous", "violation"]
    )
    expected = "VERIFIED_WITHIN_SCOPE"
    if mechanism == "missing":
        data["observations"] = []
        expected = "INCONCLUSIVE"
    elif mechanism == "conflict":
        other = copy.deepcopy(o)
        other["id"] += "-contradiction"
        other["state"] = "UNKNOWN"
        data["observations"].append(other)
        expected = "INCONCLUSIVE"
    elif mechanism == "partial":
        o["coverage"] = "PARTIAL"
        if action == "DELETE":
            expected = "INCONCLUSIVE"
    elif mechanism == "late":
        b = Bundle.model_validate(data)
        o["ingested_at"] = (b.request.audit_at + timedelta(microseconds=1)).isoformat()
        expected = "INCONCLUSIVE"
    elif mechanism == "ambiguous":
        other = copy.deepcopy(data["identities"][0])
        other["subject"] += "-other"
        data["identities"].append(other)
        expected = "INCONCLUSIVE"
    elif mechanism == "violation":
        if action in {"REDACT", "ANONYMIZE"}:
            o["fields"]["email"] = "fictional@example.test"
        else:
            o["state"] = {
                "DELETE": "PRESENT",
                "RETAIN": "ABSENT",
                "DISABLE": "ACTIVE",
                "BLOCK": "ACTIVE",
            }[action]
        expected = "NON_COMPLIANT"
    bundle = Bundle.model_validate(data)
    report = audit(bundle, "a" * 64)
    assert report.conclusion == expected
    assert not report.validation_errors
    assert check(bundle, report) == []
    if expected != "VERIFIED_WITHIN_SCOPE":
        forged = report.model_copy(update={"conclusion": "VERIFIED_WITHIN_SCOPE"})
        assert check(bundle, forged)


@pytest.mark.parametrize(
    "timestamp", ["not-a-date", "2026-01-20T12:00:00", "2026-13-20T12:00:00Z"]
)
def test_invalid_timestamps_rejected_before_proof(timestamp):
    data = copy.deepcopy(BASE)
    data["observations"][0]["observed_at"] = timestamp
    with pytest.raises(ValidationError):
        Bundle.model_validate(data)


def test_selective_citation_cannot_hide_conflicting_state():
    data = copy.deepcopy(BASE)
    other = copy.deepcopy(data["observations"][0])
    other.update(id="contradiction", state="PRESENT")
    data["observations"].append(other)
    bundle = Bundle.model_validate(data)
    report = audit(bundle, "a" * 64)
    target = bundle.targets[0]
    forged = report.model_copy(
        update={
            "conclusion": "VERIFIED_WITHIN_SCOPE",
            "assessments": (
                Assessment(
                    system=target.system,
                    resource=target.resource,
                    status="SATISFIED",
                    reason="model says so",
                    evidence=(data["observations"][0]["id"],),
                ),
            ),
        }
    )
    assert any("omitted evidence" in e for e in check(bundle, forged))
