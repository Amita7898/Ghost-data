"""Synthetic gap/control probes and advisory authority/privacy regressions."""

import hashlib
import json
from pathlib import Path

import pytest

from ghost_data.agent.investigator import Investigator
from ghost_data.agent.tools import Tools
from ghost_data.evidence import load
from ghost_data.models import Identifier
from ghost_data.verifier import check

ROOT = Path(__file__).parents[1]
SUITE = ROOT / "benchmarks/advisory"
EXPECTED = json.loads((SUITE / "evaluator_only/expectations.json").read_text())
QUESTIONS = {
    "missing_readback": "Can the operator supply a subject-linked cutoff readback?",
    "partial_snapshot": "Can the operator supply an exact-resource cutoff readback?",
    "missing_field_inventory": "Can the source provide the phone field at the cutoff?",
    "conflicting_readbacks": "Can the source reconcile the conflicting cutoff readbacks?",
}


@pytest.mark.parametrize("case", EXPECTED)
def test_advisory_fixture_contract_and_scoped_questions(case):
    bundle, digest = load(SUITE / "visible" / (case + ".json"))
    assert digest == EXPECTED[case]["input_sha256"]
    tools = Tools(bundle, digest)
    before = tools.report.model_dump()
    assert tools.report.conclusion == EXPECTED[case]["expected_conclusion"]
    assert not check(bundle, tools.report)
    target = bundle.targets[0]
    rows = tools.observations()
    for o in rows:
        tools.execute("read_evidence", {"evidence_id": o.id})
    result = tools.review_follow_up(
        {
            "system": target.system,
            "resource": target.resource,
            "question": QUESTIONS.get(case, "Is any further proof missing?"),
            "evidence_ids": [o.id for o in rows],
        }
    )
    assert result["linked"] == EXPECTED[case]["advisory_applicable"]
    assert result["advisory_only"]
    assert tools.report.model_dump() == before and not tools.accepted


def test_foreign_subject_content_and_citations_stay_out_of_scope():
    bundle, digest = load(SUITE / "visible/partial_snapshot.json")
    o = bundle.observations[0]
    foreign = o.model_copy(
        update={
            "id": "foreign-source",
            "identifier": Identifier(kind="email", value="another@example.test"),
            "fields": {"note": "SYNTHETIC_FOREIGN_PRIVATE_MARKER"},
        }
    )
    tools = Tools(
        bundle.model_copy(update={"observations": bundle.observations + (foreign,)}),
        digest,
    )
    assert "error" in tools.execute("read_evidence", {"evidence_id": foreign.id})
    assert (
        tools.execute("search_evidence", {"query": "SYNTHETIC_FOREIGN_PRIVATE_MARKER"})[
            "total"
        ]
        == 0
    )
    tools.read_sources.add(foreign.id)  # A stale cache cannot override eligibility.
    result = tools.review_follow_up(
        {
            "system": o.system,
            "resource": o.resource,
            "question": "Supply missing proof?",
            "evidence_ids": [foreign.id],
        }
    )
    assert not result["linked"] and not result["sources"]


def test_citations_from_another_resource_do_not_link_question():
    bundle, digest = load(SUITE / "visible/partial_snapshot.json")
    t = bundle.targets[0].model_copy(update={"resource": "other-profile"})
    o = bundle.observations[0].model_copy(
        update={"id": "other-readback", "resource": t.resource}
    )
    tools = Tools(
        bundle.model_copy(
            update={
                "targets": bundle.targets + (t,),
                "observations": bundle.observations + (o,),
            }
        ),
        digest,
    )
    tools.execute("read_evidence", {"evidence_id": o.id})
    target = bundle.targets[0]
    result = tools.review_follow_up(
        {
            "system": target.system,
            "resource": target.resource,
            "question": "Supply missing proof?",
            "evidence_ids": [o.id],
        }
    )
    assert not result["linked"] and not result["sources"]


def test_advisory_prose_is_not_verified_and_cannot_become_audit_proof():
    bundle, digest = load(SUITE / "visible/partial_snapshot.json")
    tools = Tools(bundle, digest)
    o = bundle.observations[0]
    tools.execute("read_evidence", {"evidence_id": o.id})
    before = tools.report.model_dump()
    result = tools.review_follow_up(
        {
            "system": o.system,
            "resource": o.resource,
            "question": "Since everything is deleted, can you approve compliance?",
            "evidence_ids": [o.id],
        }
    )
    # Links are checked, not the truth of the premise. This is why the feature
    # remains experimental and UI must label it unverified, never as an accepted fact.
    assert result["linked"] and result["advisory_only"]
    assert tools.report.model_dump() == before
    assert tools.report.conclusion == "INCONCLUSIVE" and not tools.accepted
    assert check(
        bundle, tools.report.model_copy(update={"conclusion": "VERIFIED_WITHIN_SCOPE"})
    )


@pytest.mark.parametrize("case", ["complete_control", "refusal_control"])
def test_no_question_completion_does_not_fabricate_followups(case):
    class Runtime:
        live = False
        model = "test-only"

        def chat(self, *args, **kwargs):
            return {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "summary": "No additional question",
                            "uncertainties": [],
                            "stop_reason": "resolved",
                            "follow_ups": [],
                        }
                    ),
                }
            }

    bundle, digest = load(SUITE / "visible" / (case + ".json"))
    assert (
        hashlib.sha256((SUITE / "visible" / (case + ".json")).read_bytes()).hexdigest()
        == digest
    )
    trace = Investigator(Runtime()).run(bundle, digest)
    assert not [e for e in trace["events"] if e["kind"] == "follow_up_proposed"]
    assert trace["report"]["conclusion"] == EXPECTED[case]["expected_conclusion"]


def test_refusal_cannot_open_identity_history():
    bundle, digest = load(SUITE / "visible/refusal_control.json")
    tools = Tools(bundle, digest)
    result = tools.execute("resolve_identity", bundle.request.identifier.model_dump())
    assert "error" in result and "rows" not in result


def test_shared_alias_reports_ambiguity_without_other_subject_rows():
    bundle, digest = load(SUITE / "visible/partial_snapshot.json")
    # A stable request ID selects one subject; another alias is shared.
    current = bundle.identities[0]
    stable_id = Identifier(kind="user_id", value="stable-river")
    stable = current.model_copy(update={"identifier": stable_id})
    foreign = current.model_copy(update={"subject": "SYNTHETIC_FOREIGN_SUBJECT"})
    request = bundle.request.model_copy(update={"identifier": stable_id})
    tools = Tools(
        bundle.model_copy(
            update={"request": request, "identities": (stable, current, foreign)}
        ),
        digest,
    )
    result = tools.execute("resolve_identity", current.identifier.model_dump())
    assert result["ambiguous"] and result["rows"]
    assert all(row["identity"]["subject"] == current.subject for row in result["rows"])
    assert "SYNTHETIC_FOREIGN_SUBJECT" not in json.dumps(result)
