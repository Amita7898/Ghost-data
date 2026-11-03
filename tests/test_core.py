import copy
import hashlib
import json
import sqlite3
import subprocess
import sys

import pytest
from pydantic import ValidationError

from ghost_data.authorization import classify
from ghost_data.engine import audit
from ghost_data.evidence import load
from ghost_data.models import Bundle
from ghost_data.storage import RunStore
from ghost_data.verifier import check

T = "2026-01-20T12:00:00Z"


@pytest.fixture
def data():
    identifier = {"kind": "email", "value": "river@example.test"}
    return dict(
        schema_version=1,
        request=dict(
            text="Please delete my account.",
            identifier=identifier,
            requested_at="2026-01-19T12:00:00Z",
            audit_at=T,
        ),
        identities=[
            dict(
                subject="person-river",
                identifier=identifier,
                valid_from="2025-01-01T00:00:00Z",
                recorded_at="2025-01-01T00:00:00Z",
            )
        ],
        rules=[dict(category="PROFILE", action="DELETE")],
        targets=[dict(system="accounts", resource="profile-river", category="PROFILE")],
        observations=[
            dict(
                id="readback",
                system="accounts",
                resource="profile-river",
                identifier=identifier,
                observed_at=T,
                captured_at=T,
                kind="READBACK",
                state="ABSENT",
                coverage="EXACT_RESOURCE",
            )
        ],
        scope_complete=True,
    )


def run(data):
    return audit(Bundle.model_validate(data), "a" * 64)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Do not delete my account.", "DECLINED"),
        ("Don't erase my personal information.", "DECLINED"),
        ("I am not asking for deletion.", "DECLINED"),
        ("Ne supprimez pas mon compte.", "DECLINED"),
        ("No elimines mi cuenta.", "DECLINED"),
        ("Unsubscribe me from marketing.", "NON_DELETION"),
        ("Export all my records.", "NON_DELETION"),
        ("Correct my address.", "NON_DELETION"),
        ("How do I delete my account?", "AMBIGUOUS"),
        ("If I delete my account, what happens?", "AMBIGUOUS"),
        ("I might delete my account.", "AMBIGUOUS"),
        ("Please help with my account.", "AMBIGUOUS"),
        (
            "I do not want to cancel my deletion request. Please proceed with deletion.",
            "AMBIGUOUS",
        ),
        ("Please delete my account.", "AUTHORIZED"),
        ("Can you erase my personal data?", "AUTHORIZED"),
        ("Export my data, then delete my account.", "AUTHORIZED"),
        ("Delete my account, but do not delete records required by law.", "AUTHORIZED"),
        ("Je demande la suppression de mon compte.", "AUTHORIZED"),
        ("Solicito a exclusão permanente da conta.", "AUTHORIZED"),
    ],
)
def test_intent_regressions(text, expected):
    assert classify(text) == expected


def test_scoped_absence(data):
    assert run(data).conclusion == "VERIFIED_WITHIN_SCOPE"


def test_positive_replica(data):
    data["targets"][0]["system"] = "failover"
    data["observations"][0].update(system="failover", state="PRESENT")
    result = run(data)
    assert result.conclusion == "NON_COMPLIANT"
    assert result.recommendations[0]["execution_authorized"] is False


@pytest.mark.parametrize(
    "change",
    [
        {"kind": "CLAIM"},
        {"coverage": "PARTIAL"},
        {"state": "UNKNOWN"},
        {"captured_at": "2026-01-21T12:00:00Z"},
        {"observed_at": "2026-01-18T12:00:00Z"},
        {"system": "unrelated"},
    ],
)
def test_insufficient_evidence(data, change):
    data["observations"][0].update(change)
    assert run(data).conclusion == "INCONCLUSIVE"


def test_incomplete_inventory(data):
    data["scope_complete"] = False
    assert run(data).conclusion == "INCONCLUSIVE"


def test_empty_inventory(data):
    data["targets"] = []
    assert run(data).conclusion == "INCONCLUSIVE"


def test_tombstone_fields(data):
    data["rules"][0].update(
        action="REDACT",
        required_fields=["email", "name"],
        preserve_subject_reference=True,
    )
    o = data["observations"][0]
    o.update(state="PRESENT", fields={"subject_reference": "person-river"})
    assert run(data).conclusion == "INCONCLUSIVE"
    o["fields"].update(email=None, name=None)
    assert run(data).conclusion == "VERIFIED_WITHIN_SCOPE"
    o["fields"]["email"] = "river@example.test"
    assert run(data).conclusion == "NON_COMPLIANT"


def test_anonymization_requires_unlinking(data):
    data["rules"][0].update(action="ANONYMIZE", required_fields=["email"])
    data["observations"][0].update(state="PRESENT", fields={"email": None})
    assert run(data).conclusion == "INCONCLUSIVE"
    data["observations"][0]["unlinking_verified"] = True
    assert run(data).conclusion == "VERIFIED_WITHIN_SCOPE"


def test_conditional_retention(data):
    data["rules"][0].update(action="RETAIN", condition="retention_active")
    assert run(data).conclusion == "INCONCLUSIVE"
    data["targets"][0]["conditions"] = {"retention_active": True}
    assert run(data).conclusion == "NON_COMPLIANT"
    data["observations"][0]["state"] = "PRESENT"
    assert run(data).conclusion == "VERIFIED_WITHIN_SCOPE"
    data["targets"][0]["conditions"]["retention_active"] = False
    assert run(data).conclusion == "INCONCLUSIVE"


def test_backup_requires_archive(data):
    data["rules"][0]["action"] = "BLOCK"
    data["observations"][0]["state"] = "BLOCKED"
    assert run(data).conclusion == "INCONCLUSIVE"
    data["observations"][0]["archive_present"] = True
    assert run(data).conclusion == "VERIFIED_WITHIN_SCOPE"


def test_conflicting_readbacks(data):
    other = copy.deepcopy(data["observations"][0])
    other.update(id="contradiction", state="PRESENT")
    data["observations"].append(other)
    result = run(data)
    assert result.conclusion == "INCONCLUSIVE"
    forged = result.model_copy(
        update={
            "assessments": (
                result.assessments[0].model_copy(
                    update={"status": "SATISFIED", "evidence": ("readback",)}
                ),
            ),
            "conclusion": "VERIFIED_WITHIN_SCOPE",
        }
    )
    assert check(Bundle.model_validate(data), forged)


def test_historical_identity_and_reassignment(data):
    data["identities"][0]["valid_to"] = "2026-01-10T00:00:00Z"
    new = copy.deepcopy(data["identities"][0])
    new.update(valid_from="2026-01-10T00:00:00Z", valid_to=None)
    new["identifier"] = {"kind": "user_id", "value": "river-internal"}
    data["identities"].append(new)
    data["observations"][0]["identifier"] = new["identifier"]
    assert run(data).conclusion == "VERIFIED_WITHIN_SCOPE"
    reassigned = copy.deepcopy(data["identities"][0])
    reassigned.update(
        subject="another-person", valid_from="2026-01-11T00:00:00Z", valid_to=None
    )
    data["identities"].append(reassigned)
    assert run(data).conclusion == "INCONCLUSIVE"


def test_future_identity_mapping(data):
    data["identities"][0]["recorded_at"] = "2026-01-21T00:00:00Z"
    assert run(data).conclusion == "INCONCLUSIVE"


def test_declined_has_no_plan(data):
    data["request"]["text"] = "No elimines mi cuenta."
    result = run(data)
    assert (
        result.conclusion == "NOT_APPLICABLE"
        and not result.assessments
        and not result.recommendations
    )


def test_independent_checker_rejects_forged_pass(data):
    data["observations"][0]["kind"] = "CLAIM"
    result = run(data)
    forged = result.model_copy(
        update={
            "conclusion": "VERIFIED_WITHIN_SCOPE",
            "assessments": (
                result.assessments[0].model_copy(
                    update={"status": "SATISFIED", "evidence": ("readback",)}
                ),
            ),
        }
    )
    assert check(Bundle.model_validate(data), forged)


def test_dependency_order_and_cycle(data):
    data["observations"][0]["state"] = "PRESENT"
    data["rules"].append(dict(category="FLOW", action="DISABLE"))
    data["targets"].append(dict(system="sync", resource="connector", category="FLOW"))
    data["targets"][0]["depends_on"] = [dict(system="sync", resource="connector")]
    o = copy.deepcopy(data["observations"][0])
    o.update(id="flow", system="sync", resource="connector", state="ACTIVE")
    data["observations"].append(o)
    assert [r["action"] for r in run(data).recommendations] == ["DISABLE", "DELETE"]
    data["targets"][1]["depends_on"] = [
        dict(system="accounts", resource="profile-river")
    ]
    assert not run(data).recommendations


def test_ingestion_hash_and_sqlite(data, tmp_path):
    path = tmp_path / "bundle.json"
    raw = json.dumps(data).encode()
    path.write_bytes(raw)
    bundle, digest = load(path)
    assert digest == hashlib.sha256(raw).hexdigest()
    result = audit(bundle, digest)
    assert "#/observations/0" in result.provenance["readback"]
    db = tmp_path / "history.sqlite"
    store = RunStore(db)
    run_id = store.save(raw, result)
    assert json.loads(store.read(run_id))["conclusion"] == result.conclusion
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 5
        assert conn.execute("SELECT artifact FROM runs").fetchone()[0] == raw
    assert audit(bundle, digest) == result


def test_cli(data, tmp_path):
    path = tmp_path / "input.json"
    path.write_text(json.dumps(data))
    proc = subprocess.run(
        [sys.executable, "-m", "ghost_data.cli", str(path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["conclusion"] == "VERIFIED_WITHIN_SCOPE"


@pytest.mark.parametrize(
    "mutation", ["duplicate", "naive", "extra", "interval", "capture"]
)
def test_schema_rejects_bad_data(data, mutation):
    if mutation == "duplicate":
        data["observations"] *= 2
    if mutation == "naive":
        data["request"]["audit_at"] = "2026-01-20T12:00:00"
    if mutation == "extra":
        data["golden_answer"] = "COMPLETE"
    if mutation == "interval":
        data["identities"][0]["valid_to"] = "2024-01-01T00:00:00Z"
    if mutation == "capture":
        data["observations"][0]["captured_at"] = "2025-01-01T00:00:00Z"
    with pytest.raises(ValidationError):
        Bundle.model_validate(data)


def test_unresolved_dependency_blocks_plan(data):
    data["observations"][0]["state"] = "PRESENT"
    data["targets"][0]["depends_on"] = [dict(system="sync", resource="unknown")]
    result = run(data)
    assert not result.recommendations and result.unresolved


def test_verifier_rejects_unsafe_recommendation(data):
    data["observations"][0]["state"] = "PRESENT"
    report = run(data)
    forged = report.model_copy(
        update={
            "recommendations": (
                {
                    "system": "accounts",
                    "resource": "profile-river",
                    "action": "RETAIN",
                    "execution_authorized": True,
                },
            )
        }
    )
    assert check(Bundle.model_validate(data), forged)


def test_row_ownership_does_not_spread(data):
    data["observations"][0]["identifier"] = {
        "kind": "email",
        "value": "someone-else@example.test",
    }
    assert run(data).conclusion == "INCONCLUSIVE"


def test_boolean_strings_rejected(data):
    data["scope_complete"] = "true"
    with pytest.raises(ValidationError):
        Bundle.model_validate(data)


def test_duplicate_json_keys(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="duplicate"):
        load(path)


def test_oversized_input(tmp_path):
    path = tmp_path / "large.json"
    path.write_bytes(b" " * 5_000_001)
    with pytest.raises(ValueError, match="5 MB"):
        load(path)


def test_hash_mismatch_not_persisted(data, tmp_path):
    store = RunStore(tmp_path / "history.sqlite")
    with pytest.raises(ValueError, match="artifact bytes"):
        store.save(b"{}", run(data))
