"""Additional consent-context probes; prior intent fixtures remain unchanged."""

import json
from pathlib import Path

import pytest

from ghost_data.agent.tools import Tools
from ghost_data.authorization import classify
from ghost_data.engine import audit
from ghost_data.evidence import load_bytes
from ghost_data.verifier import check

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("I refuse. Delete my account? No.", "DECLINED"),
        ("Please remove my account from your marketing mailing list.", "NON_DELETION"),
        ("Remove my data from your newsletter list.", "NON_DELETION"),
        ("I do not consent. Delete my account is not something I want.", "DECLINED"),
        ("I am not authorizing you to delete my account.", "DECLINED"),
        ("I cannot authorize you to delete my account.", "DECLINED"),
        ("I can't consent to you asking me to delete my data.", "DECLINED"),
        ("I am not authorising you to erase my personal data.", "DECLINED"),
        ("No, delete my account is not what I want.", "DECLINED"),
        ("Delete my account? No thanks.", "DECLINED"),
        ("Delete my account?", "AMBIGUOUS"),
        ("Hello. Erase my data?", "AMBIGUOUS"),
        ("Delete my account is just the button label.", "AMBIGUOUS"),
        ("Delete my account is something my friend mentioned.", "AMBIGUOUS"),
        ("Delete my account tomorrow.", "AMBIGUOUS"),
        ("The button says delete my account.", "AMBIGUOUS"),
        ("I see the wording delete my account.", "AMBIGUOUS"),
        ("My colleague wrote: delete my account.", "AMBIGUOUS"),
        ("The dialog displays delete my account.", "AMBIGUOUS"),
        ("I clicked 'delete my account' by mistake.", "AMBIGUOUS"),
        ("What happens after “delete my data”?", "AMBIGUOUS"),
        ('The screen says "I want my account deleted."', "AMBIGUOUS"),
        ("Someone requested that I want my account deleted.", "AMBIGUOUS"),
        ("If I consent later, please delete my account.", "AMBIGUOUS"),
    ],
)
def test_non_authorizing_context_cannot_create_an_audit_plan(text, expected):
    data = json.loads((ROOT / "examples/scoped_absence.json").read_bytes())
    data["request"]["text"] = text
    bundle, digest = load_bytes(json.dumps(data).encode())
    assert classify(text) == expected
    report = audit(bundle, digest)
    assert report.authorization != "AUTHORIZED"
    assert report.conclusion != "VERIFIED_WITHIN_SCOPE"
    assert not report.assessments and not report.recommendations
    tools = Tools(bundle, digest)
    assert tools.execute("search_evidence", {})["total"] == 0
    assert not tools.review_follow_up(
        {
            "system": bundle.targets[0].system,
            "resource": bundle.targets[0].resource,
            "question": "Can deletion be proven?",
            "evidence_ids": [],
        }
    )["linked"]
    assert check(
        bundle, report.model_copy(update={"conclusion": "VERIFIED_WITHIN_SCOPE"})
    )


@pytest.mark.parametrize(
    "text",
    [
        "Please delete my account.",
        "Please delete my account. Remove me from the mailing list.",
        "I'd like you to delete my account.",
        "I want my account deleted.",
        "Can you delete my account, please?",
        "Could you please erase all my personal data?",
        "Please do delete my account.",
        "Delete my account. How long will it take?",
        "Don't send me emails. Delete my data.",
    ],
)
def test_supported_requests_still_authorize_only_audit(text):
    assert classify(text) == "AUTHORIZED"
