"""Model questions are advisory; passing citation checks never establishes truth."""

import json
from datetime import timedelta
from pathlib import Path

import pytest

from ghost_data.agent.investigator import Investigator
from ghost_data.agent.tools import Tools
from ghost_data.evidence import load


@pytest.fixture
def tools():
    b, d = load(Path(__file__).parents[1] / "examples/scoped_absence.json")
    o = b.observations[0].model_copy(update={"coverage": "PARTIAL"})
    return Tools(b.model_copy(update={"observations": (o,)}), d)


def proposal(t, **updates):
    o = t.bundle.observations[0]
    return {
        "system": o.system,
        "resource": o.resource,
        "question": "Can the operator supply a complete, subject-linked readback at the cutoff?",
        "evidence_ids": [o.id],
        **updates,
    }


def test_follow_up_requires_actually_read_source(tools):
    p = proposal(tools)
    assert not tools.review_follow_up(p)["linked"]
    tools.execute("read_evidence", {"evidence_id": p["evidence_ids"][0]})
    result = tools.review_follow_up(p)
    assert result["linked"] and result["advisory_only"] and result["sources"]
    assert tools.report.conclusion == "INCONCLUSIVE"


@pytest.mark.parametrize(
    "updates",
    [{"resource": "invented"}, {"evidence_ids": ["invented"]}, {"evidence_ids": []}],
)
def test_follow_up_rejects_unlinked_or_uncited_questions(tools, updates):
    tools.execute("read_evidence", {"evidence_id": tools.bundle.observations[0].id})
    assert not tools.review_follow_up(proposal(tools, **updates))["linked"]


def test_no_evidence_allows_scoped_missing_proof_question(tools):
    tools.bundle = tools.bundle.model_copy(update={"observations": ()})
    assert tools.review_follow_up(proposal_from_target(tools))["linked"]


def proposal_from_target(t):
    target = t.bundle.targets[0]
    return {
        "system": target.system,
        "resource": target.resource,
        "question": "Supply a subject-attributed cutoff readback?",
        "evidence_ids": [],
    }


def test_late_and_other_resource_sources_cannot_ground_questions(tools):
    o = tools.bundle.observations[0]
    late = o.model_copy(
        update={"ingested_at": tools.bundle.request.audit_at + timedelta(seconds=1)}
    )
    tools.bundle = tools.bundle.model_copy(update={"observations": (late,)})
    tools.read_sources.add(o.id)  # Simulate stale cache; eligibility is rechecked.
    assert not tools.review_follow_up(proposal(tools))["linked"]


def test_satisfied_obligation_cannot_be_misrepresented_as_unresolved(tools):
    o = tools.bundle.observations[0].model_copy(update={"coverage": "EXACT_RESOURCE"})
    t = Tools(tools.bundle.model_copy(update={"observations": (o,)}), tools.digest)
    t.execute("read_evidence", {"evidence_id": o.id})
    assert not t.review_follow_up(proposal(t))["linked"]


def test_proposed_question_is_recorded_without_becoming_audit_fact(tools):
    class Runtime:
        live = False
        model = "test-only"

        def chat(self, *args, **kwargs):
            return {
                "message": {
                    "role": "assistant",
                    "content": json.dumps(
                        {
                            "summary": "Missing coverage",
                            "uncertainties": ["Partial snapshot"],
                            "stop_reason": "insufficient_evidence",
                            "follow_ups": [proposal(tools)],
                        }
                    ),
                }
            }

    trace = Investigator(Runtime()).run(tools.bundle, tools.digest)
    events = [e for e in trace["events"] if e["kind"] == "follow_up_proposed"]
    assert len(events) == 1 and not events[0]["data"]["linked"]
    assert trace["report"]["conclusion"] == "INCONCLUSIVE"
    assert not trace["accepted"]


def test_packaged_v4_prompt_preserves_original_hash():
    import hashlib
    from importlib.resources import files

    prompt = (
        files("ghost_data.agent")
        .joinpath("prompts/investigator-v4.txt")
        .read_text()
        .removesuffix("\n")
    )
    # Published recordings contain the actual v4 prompt digest, not its text.
    root = Path(__file__).parents[1]
    recordings = [
        json.loads(p.read_text()) for p in (root / "demo").glob("*-live.json")
    ]
    hashes = {
        t["prompt_sha256"]
        for t in recordings
        if t["prompt_version"] == "investigator-v4"
    }
    assert hashes and hashes == {hashlib.sha256(prompt.encode()).hexdigest()}
