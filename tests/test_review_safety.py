"""Regressions for verified review findings; runtime stubs are test-only."""

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from ghost_data.agent.investigator import Investigator
from ghost_data.agent.persistence import save_investigation
from ghost_data.agent.replay import replay, save_trace
from ghost_data.agent.tools import Tools
from ghost_data.engine import audit
from ghost_data.evidence import load, load_bytes
from ghost_data.identity import resolve, subject_for_request
from ghost_data.storage import RunStore
from ghost_data.web.app import create_app
from ghost_data.web.models import CreateInvestigation
from ghost_data.web.service import Service

ROOT = Path(__file__).parents[1]


class Runtime:
    live = False
    model = "test-only"

    def ready(self):
        return {}

    def chat(self, *args, **kwargs):
        return {
            "message": {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "summary": "Source examined",
                        "uncertainties": [],
                        "stop_reason": "resolved",
                    }
                ),
            },
            "prompt_eval_count": 12,
            "eval_count": 8,
        }


@pytest.fixture
def source():
    return load(ROOT / "examples/remaining_replica.json")


@pytest.mark.parametrize("crash", [False, True])
def test_verifier_failure_preserves_trace_without_success(
    source, monkeypatch, tmp_path, crash
):
    def reject(*args):
        if crash:
            raise RuntimeError("private implementation detail")
        return ["Forced independent proof rejection"]

    monkeypatch.setattr("ghost_data.agent.investigator.check", reject)
    b, d = source
    events = []
    trace = Investigator(Runtime()).run(b, d, on_event=events.append)
    assert trace["status"] == "verification_failed" and trace["report"] is None
    assert trace["usage"]["model_calls"] == 1 and trace["usage"]["input_tokens"] == 12
    assert trace["validation_errors"] and trace["events"] == events
    assert events[-1]["kind"] == "verification_failed"
    assert any(e["kind"] == "model_summary" for e in events)
    assert not any(e["kind"] == "deterministic_conclusion" for e in events)
    assert "private implementation detail" not in str(trace)
    raw = (ROOT / "examples/remaining_replica.json").read_bytes()
    save_investigation(tmp_path / "run.sqlite", raw, trace)
    with sqlite3.connect(tmp_path / "run.sqlite") as db:
        assert (
            json.loads(db.execute("select trace from agent_runs").fetchone()[0])
            == trace
        )
    # Constructed fixture validates serialization only; never shipped as a live recording.
    trace["execution"] = "live_local"
    path = tmp_path / "failure-fixture.json"
    save_trace(trace, path)
    value = replay(path)
    assert value["report"] is None and value["recorded_status"] == "verification_failed"


def test_web_proof_failure_is_terminal_and_not_an_ollama_error(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "ghost_data.agent.investigator.check", lambda *args: ["Forced proof rejection"]
    )
    app = create_app(ROOT, tmp_path / "data", runtime_factory=Runtime, offline=False)
    with TestClient(app, base_url="http://127.0.0.1") as c:
        inv = c.post(
            "/api/v1/investigations", json={"title": "Proof failure regression"}
        ).json()
        artifact = c.put(
            "/api/v1/investigations/" + inv["id"] + "/evidence",
            content=(ROOT / "examples/remaining_replica.json").read_bytes(),
            headers={"Content-Type": "application/json"},
        ).json()
        result = c.post(
            "/api/v1/investigations/" + inv["id"] + "/runs",
            json={"artifact_id": artifact["id"]},
            headers={"Idempotency-Key": "proof-failure-case"},
        ).json()
        for _ in range(100):
            run = c.get("/api/v1/runs/" + result["id"]).json()
            if run["status"] == "verification_failed":
                break
            time.sleep(0.01)
        assert (
            run["status"] == "verification_failed"
            and run["report"] is None
            and run["conclusion"] is None
        )
        assert (
            "verification failed" in run["error"].lower()
            and "Ollama" not in run["error"]
        )
        events = c.get("/api/v1/runs/" + run["id"] + "/events").json()
        assert any(
            e["kind"] == "verification_failed" and e["data"]["errors"] for e in events
        )
        stream = c.get("/api/v1/runs/" + run["id"] + "/stream")
        assert "event: end" in stream.text
        with sqlite3.connect(app.state.repo.db) as db:
            trace = json.loads(
                db.execute(
                    "select trace from web_runs where id=?", (run["id"],)
                ).fetchone()[0]
            )
        assert trace["validation_errors"] == ["Forced proof rejection"]
        # A terminal failure ignores late worker events and completion writes.
        app.state.repo.finish(run["id"], status="completed")
        assert app.state.repo.run(run["id"])["status"] == "verification_failed"


def test_load_bytes_matches_file_and_rejects_duplicate_keys(source, tmp_path):
    raw = (ROOT / "examples/remaining_replica.json").read_bytes()
    assert load_bytes(raw) == source
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_bytes(b'{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="5 MB"):
        load_bytes(b" " * 5_000_001)


def test_web_parse_does_not_write_a_temporary_file(tmp_path, monkeypatch):
    raw = (ROOT / "examples/remaining_replica.json").read_bytes()
    service = Service(SimpleNamespace(root=tmp_path), ROOT)

    def no_file(*args, **kwargs):
        raise AssertionError("Parser attempted a filesystem operation")

    try:
        with monkeypatch.context() as patch:
            patch.setattr(Path, "open", no_file)
            assert service.parse(raw)[1] == hashlib.sha256(raw).hexdigest()
    finally:
        service.shutdown()


def test_search_uses_values_and_preserves_identifier_recall(source):
    b, d = source
    t = Tools(b, d)
    o = b.observations[0]
    for key in ("fields", "kind", "state", "identifier"):
        assert t.execute("search_evidence", {"query": key})["total"] == 0
    for value in (o.resource, o.system, o.id, o.identifier.value, o.state):
        found = t.execute("search_evidence", {"query": value})
        assert found["total"] == 1 and found["items"][0]["id"] == o.id
    b = b.model_copy(
        update={
            "observations": (
                o.model_copy(
                    update={"fields": {"note": "The kind operator checked the state."}}
                ),
            )
        }
    )
    assert Tools(b, d).execute("search_evidence", {"query": "kind"})["total"] == 1


@pytest.mark.parametrize(
    "host", ["[::1]:8000", "[::1]", "localhost:8000", "127.0.0.1:8000"]
)
def test_loopback_host_parsing_accepts_valid_authorities(tmp_path, host):
    with TestClient(
        create_app(ROOT, tmp_path / "data", offline=True), base_url="http://127.0.0.1"
    ) as c:
        assert c.get("/api/v1/health", headers={"Host": host}).status_code == 200


@pytest.mark.parametrize(
    "host",
    [
        "[::1].evil.test",
        "::1",
        "localhost@evil.test",
        "[2001:db8::1]:8000",
        "[::1]:99999",
        "localhost/evil",
    ],
)
def test_host_parsing_stays_fail_closed(tmp_path, host):
    with TestClient(
        create_app(ROOT, tmp_path / "data", offline=True), base_url="http://127.0.0.1"
    ) as c:
        assert c.get("/api/v1/health", headers={"Host": host}).status_code == 403


def test_report_escapes_error_text(tmp_path):
    app = create_app(ROOT, tmp_path / "data", offline=True)
    with TestClient(app, base_url="http://127.0.0.1") as c:
        run = c.post("/api/v1/demos/receipt/open").json()
        app.state.repo.update(
            run["id"], error="<script>oops</script> [bad](javascript:alert(1))"
        )
        text = c.get("/api/v1/runs/" + run["id"] + "/report").text
        assert "<script>" not in text and "\\[bad\\]" in text


def test_cli_and_agent_connections_are_closed(source, tmp_path, monkeypatch):
    import ghost_data.storage as storage

    original = sqlite3.connect
    opened = []

    class Connection(sqlite3.Connection):
        closed = False

        def close(self):
            self.closed = True
            return super().close()

    def connect(*args, **kwargs):
        result = original(*args, factory=Connection, **kwargs)
        opened.append(result)
        return result

    monkeypatch.setattr(storage.sqlite3, "connect", connect)
    b, d = source
    raw = (ROOT / "examples/remaining_replica.json").read_bytes()
    report = audit(b, d)
    store = RunStore(tmp_path / "store.sqlite")
    id = store.save(raw, report)
    assert json.loads(store.read(id))["conclusion"] == "NON_COMPLIANT"
    trace = Investigator(Runtime()).run(b, d)
    save_investigation(tmp_path / "agent.sqlite", raw, trace)
    assert len(opened) >= 5 and all(c.closed for c in opened)


def test_reassigned_historical_email_cannot_select_the_previous_subject(source):
    b, d = source
    first = b.identities[0]
    at = b.request.requested_at
    old = first.model_copy(update={"valid_to": at})
    current = first.model_copy(
        update={"subject": "different-person", "valid_from": at, "valid_to": None}
    )
    b = b.model_copy(update={"identities": (old, current)})
    assert resolve(first.identifier, at, b.request.audit_at, b.identities) == {
        "different-person"
    }
    assert subject_for_request(b) is None
    assert audit(b, d).conclusion == "INCONCLUSIVE"


def test_proof_failure_preserves_tool_calls_and_accepted_hypotheses(
    source, monkeypatch
):
    b, d = source
    o = b.observations[0]

    class InvestigatingRuntime(Runtime):
        calls = 0

        def chat(self, *args, **kwargs):
            self.calls += 1
            if self.calls == 1:
                return {
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "function": {
                                    "name": "submit_hypothesis",
                                    "arguments": {
                                        "system": o.system,
                                        "resource": o.resource,
                                        "evidence_id": o.id,
                                        "claim": "STATE",
                                        "value": o.state,
                                    },
                                }
                            }
                        ],
                    },
                    "prompt_eval_count": 12,
                    "eval_count": 8,
                }
            return super().chat(*args, **kwargs)

    monkeypatch.setattr(
        "ghost_data.agent.investigator.check", lambda *args: ["Forced proof failure"]
    )
    trace = Investigator(InvestigatingRuntime()).run(b, d)
    assert trace["report"] is None and trace["status"] == "verification_failed"
    assert trace["tool_calls"] == 1 and trace["usage"]["model_calls"] == 2
    assert len(trace["accepted"]) == 1 and trace["accepted"][0]["source"]
    assert any(e["kind"] == "hypothesis_validated" for e in trace["events"])


def test_proof_failure_is_not_masked_by_a_concurrent_cancel(tmp_path):
    app = create_app(ROOT, tmp_path / "data", offline=True)
    repo = app.state.repo
    try:
        inv = repo.create(CreateInvestigation(title="Cancel race"))
        artifact = app.state.service.ingest(
            inv["id"],
            (ROOT / "examples/remaining_replica.json").read_bytes(),
            "fixture.json",
            "upload",
        )
        run, _ = repo.start(inv["id"], artifact["id"], "live", "test-only", {})
        repo.request_cancel(run["id"])
        repo.finish(
            run["id"],
            status="verification_failed",
            report=None,
            conclusion=None,
            error="Independent proof failed",
        )
        assert repo.run(run["id"])["status"] == "verification_failed"
    finally:
        app.state.service.shutdown()
