import json
import threading
import time
from datetime import UTC
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ghost_data.web.app import create_app

ROOT = Path(__file__).parents[1]


@pytest.fixture
def app(tmp_path):
    return create_app(ROOT, tmp_path / "data", offline=True)


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://127.0.0.1") as c:
        yield c


def create(c):
    return c.post(
        "/api/v1/investigations", json={"title": "Synthetic investigation"}
    ).json()["id"]


def upload(c, id, name="evidence.json", raw=None):
    return c.put(
        f"/api/v1/investigations/{id}/evidence",
        content=raw or (ROOT / "examples/remaining_replica.json").read_bytes(),
        headers={"Content-Type": "application/json", "X-Filename": name},
    )


def test_replay_works_without_runtime(client, app):
    app.state.service.runtime_factory = lambda: (_ for _ in ()).throw(
        AssertionError("Runtime used in replay")
    )
    response = client.post("/api/v1/demos/receipt/open")
    assert response.status_code == 201
    run = response.json()
    assert run["mode"] == "replay" and run["status"] == "completed"
    assert run["report"]["conclusion"] == "VERIFIED_WITHIN_SCOPE"
    events = client.get(f"/api/v1/runs/{run['id']}/events").json()
    assert any(e["kind"] == "hypothesis_validated" for e in events)
    assert (
        "VERIFIED_WITHIN_SCOPE" in client.get(f"/api/v1/runs/{run['id']}/report").text
    )


def test_persistence_restart(tmp_path):
    data = tmp_path / "db"
    with TestClient(
        create_app(ROOT, data, offline=True), base_url="http://127.0.0.1"
    ) as c:
        id = c.post("/api/v1/demos/replica/open").json()["id"]
    with TestClient(
        create_app(ROOT, data, offline=True), base_url="http://127.0.0.1"
    ) as c:
        assert c.get("/api/v1/runs/" + id).json()["status"] == "completed"
        assert c.get("/api/v1/runs/" + id + "/events").json()


def test_upload_and_exact_source_preview(client):
    id = create(client)
    a = upload(client, id).json()
    fragment = client.get(
        f"/api/v1/artifacts/{a['id']}/fragment", params={"pointer": "/observations/0"}
    ).json()
    assert fragment["source"] == f"sha256:{a['sha256']}#/observations/0"
    assert "PRESENT" in fragment["text"]
    assert client.get("/api/v1/investigations/" + id + "/context").json()[
        "relationships"
    ]


@pytest.mark.parametrize(
    "name", ["../private.json", "file.html", "a\\b.json", "truth.zip"]
)
def test_bad_filename(client, name):
    assert upload(client, create(client), name).status_code == 400


@pytest.mark.parametrize(
    "raw", [b'{"truth":true}', b'{"schema_version":1,"schema_version":1}', b"not json"]
)
def test_invalid_bundle(client, raw):
    assert upload(client, create(client), raw=raw).status_code == 422


def test_oversize_and_media_type(client):
    id = create(client)
    assert upload(client, id, raw=b"x" * 5_000_001).status_code == 413
    assert (
        client.put(
            "/api/v1/investigations/" + id + "/evidence",
            content=b"abc",
            headers={"Content-Type": "image/png"},
        ).status_code
        == 415
    )


def test_cross_origin_and_rebinding(client):
    assert (
        client.get(
            "/api/v1/investigations", headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/v1/investigations", headers={"Host": "evil.example"}
        ).status_code
        == 403
    )


def test_unsafe_fragment_and_unknown_demo(client):
    a = upload(client, create(client)).json()
    assert (
        client.get(
            f"/api/v1/artifacts/{a['id']}/fragment?pointer=/../../secret"
        ).status_code
        == 400
    )
    assert client.post("/api/v1/demos/private/open").status_code == 404


def test_sse_reconnection_uses_persisted_cursor(client):
    run = client.post("/api/v1/demos/receipt/open").json()
    url = f"/api/v1/runs/{run['id']}"
    events = client.get(url + "/events").json()
    last = events[4]["seq"]
    response = client.get(url + "/stream", headers={"Last-Event-ID": str(last)})
    ids = [
        int(line[4:]) for line in response.text.splitlines() if line.startswith("id: ")
    ]
    assert ids == [e["seq"] for e in events if e["seq"] > last]
    assert "event: end" in response.text


def test_offline_start_is_honest(client):
    id = create(client)
    a = upload(client, id).json()
    assert not client.get("/api/v1/runtime").json()["available"]
    assert (
        client.post(
            f"/api/v1/investigations/{id}/runs",
            json={"artifact_id": a["id"]},
            headers={"Idempotency-Key": "offline-test"},
        ).status_code
        == 503
    )


def test_scope_and_cutoff_are_explicit_effective_inputs(client):
    b = json.loads((ROOT / "examples/remaining_replica.json").read_text())
    c = client.post(
        "/api/v1/investigations",
        json={
            "title": "Scoped",
            "audit_at": "2026-01-20T12:00:01Z",
            "scope": [
                json.dumps([t["system"], t["resource"]], separators=(",", ":"))
                for t in b["targets"]
            ],
        },
    ).json()
    a = upload(client, c["id"]).json()
    assert a["source"] == "configured"
    context = client.get("/api/v1/investigations/" + c["id"] + "/context").json()
    assert context["bundle"]["request"]["audit_at"] == "2026-01-20T12:00:01Z"
    assert (
        len(client.get("/api/v1/investigations/" + c["id"] + "/evidence").json()) == 2
    )


def test_live_failure_and_idempotency(tmp_path):
    gate = threading.Event()

    class Unavailable:
        model = "test-only"
        live = False

        def ready(self):
            gate.wait(2)
            raise ConnectionError("test failure")

    app = create_app(
        ROOT, tmp_path / "data", runtime_factory=Unavailable, offline=False
    )
    with TestClient(app, base_url="http://127.0.0.1") as c:
        id = create(c)
        a = upload(c, id).json()
        url = f"/api/v1/investigations/{id}/runs"
        body = {"artifact_id": a["id"]}
        headers = {"Idempotency-Key": "same-request"}
        first = c.post(url, json=body, headers=headers)
        assert first.status_code == 202
        same = c.post(url, json=body, headers=headers)
        assert same.json()["id"] == first.json()["id"]
        assert (
            c.post(
                url, json=body, headers={"Idempotency-Key": "another-key"}
            ).status_code
            == 409
        )
        gate.set()
        for _ in range(100):
            run = c.get("/api/v1/runs/" + first.json()["id"]).json()
            if run["status"] == "failed":
                break
            time.sleep(0.01)
        assert run["status"] == "failed" and run["report"] is None


def test_cancellation_is_not_completion(tmp_path):
    gate = threading.Event()

    class Blocked:
        model = "test-only"
        live = False

        def ready(self):
            gate.wait(2)
            return {}

        def chat(self, *a, **kw):
            raise AssertionError("Cancelled run must not infer")

    app = create_app(ROOT, tmp_path / "data", runtime_factory=Blocked, offline=False)
    with TestClient(app, base_url="http://127.0.0.1") as c:
        id = create(c)
        a = upload(c, id).json()
        run = c.post(
            f"/api/v1/investigations/{id}/runs",
            json={"artifact_id": a["id"]},
            headers={"Idempotency-Key": "cancel-request"},
        ).json()
        assert (
            c.post(f"/api/v1/runs/{run['id']}/cancel").json()["status"] == "cancelling"
        )
        gate.set()
        for _ in range(100):
            result = c.get("/api/v1/runs/" + run["id"]).json()
            if result["status"] == "cancelled":
                break
            time.sleep(0.01)
        assert result["status"] == "cancelled"


def test_recovery_cannot_be_overwritten_by_stale_worker(client, app):
    id = create(client)
    a = upload(client, id).json()
    repo = app.state.repo
    run, _ = repo.start(id, a["id"], "live", "test", {}, "recovery-case")
    repo.recover()
    before = repo.events(run["id"])
    repo.finish(run["id"], status="completed", conclusion="VERIFIED_WITHIN_SCOPE")
    repo.event(run["id"], {"kind": "tool_returned", "data": {"stale": True}})
    assert repo.run(run["id"])["status"] == "interrupted"
    assert repo.events(run["id"]) == before


def test_cancel_wins_completion_race(client, app):
    id = create(client)
    a = upload(client, id).json()
    repo = app.state.repo
    run, _ = repo.start(id, a["id"], "live", "test", {}, "cancel-race")
    repo.request_cancel(run["id"])
    repo.finish(run["id"], status="completed")
    assert repo.run(run["id"])["status"] == "cancelled"


def test_tampered_artifact_is_not_previewed_or_admitted(client, app):
    id = create(client)
    a = upload(client, id).json()
    app.state.repo.path(a["id"]).write_text("{}")
    assert client.get(f"/api/v1/artifacts/{a['id']}/content").status_code == 409
    assert client.get("/api/v1/investigations/" + id + "/context").status_code == 409


def test_bounded_scope_rejects_unknown_resources_without_storing(client):
    inv = client.post(
        "/api/v1/investigations",
        json={"title": "Bad scope", "scope": ['["invented","resource"]']},
    ).json()
    assert upload(client, inv["id"]).status_code == 422
    assert client.get("/api/v1/investigations/" + inv["id"] + "/evidence").json() == []


def test_unedited_cutoff_keeps_original_subsecond_precision(client):
    b = json.loads((ROOT / "examples/remaining_replica.json").read_text())
    b["request"]["audit_at"] = "2026-01-20T12:00:00.123456Z"
    b["observations"][0]["observed_at"] = b["observations"][0]["captured_at"] = b[
        "request"
    ]["audit_at"]
    id = create(client)
    a = upload(client, id, raw=json.dumps(b).encode()).json()
    assert a["source"] == "upload"
    assert (
        client.get("/api/v1/investigations/" + id + "/context").json()["bundle"][
            "request"
        ]["audit_at"]
        == b["request"]["audit_at"]
    )


def test_host_events_use_elapsed_time_not_zero(client, app):
    from datetime import datetime, timedelta

    id = create(client)
    a = upload(client, id).json()
    repo = app.state.repo
    run, _ = repo.start(id, a["id"], "live", "test", {}, "elapsed-case")
    with repo.connect() as db:
        db.execute(
            "UPDATE web_runs SET created_at=? WHERE id=?",
            (
                (datetime.now(UTC) - timedelta(seconds=5)).isoformat(),
                run["id"],
            ),
        )
    repo.request_cancel(run["id"])
    repo.finish(run["id"], status="completed")
    assert all(e["elapsed_seconds"] >= 5 for e in repo.events(run["id"]))


def test_http_client_cannot_submit_a_forged_final_report(client):
    id = create(client)
    a = upload(client, id).json()
    response = client.post(
        f"/api/v1/investigations/{id}/runs",
        json={
            "artifact_id": a["id"],
            "report": {"conclusion": "VERIFIED_WITHIN_SCOPE"},
        },
        headers={"Idempotency-Key": "forged-report"},
    )
    assert response.status_code == 422
    assert client.get("/api/v1/runs").json() == []


def test_changed_demo_recording_is_rejected_before_import(tmp_path):
    import shutil

    root = tmp_path / "project"
    (root / "demo").mkdir(parents=True)
    (root / "examples").mkdir()
    for name in ("RECORDING_SHA256.json", "receipt-absent-v4-live.json"):
        shutil.copyfile(ROOT / "demo" / name, root / "demo" / name)
    shutil.copyfile(
        ROOT / "examples/prose_receipt.json", root / "examples/prose_receipt.json"
    )
    trace_path = root / "demo/receipt-absent-v4-live.json"
    data = json.loads(trace_path.read_text())
    data["report"]["conclusion"] = "NON_COMPLIANT"
    trace_path.write_text(json.dumps(data))
    with TestClient(
        create_app(root, tmp_path / "data", offline=True), base_url="http://127.0.0.1"
    ) as c:
        assert c.post("/api/v1/demos/receipt/open").status_code == 422
        assert c.get("/api/v1/investigations").json() == []


def test_future_evidence_is_visible_but_marked_ineligible(client):
    b = json.loads((ROOT / "examples/remaining_replica.json").read_text())
    b["observations"][0]["observed_at"] = b["observations"][0]["captured_at"] = (
        "2026-01-21T12:00:00Z"
    )
    id = create(client)
    assert upload(client, id, raw=json.dumps(b).encode()).status_code == 201
    context = client.get("/api/v1/investigations/" + id + "/context").json()
    assert (
        "observed_at_after_cutoff" in context["eligibility"][b["observations"][0]["id"]]
    )
    assert not context["relationships"]


def test_source_preview_rejects_symlink_even_with_matching_bytes(client, app, tmp_path):
    id = create(client)
    a = upload(client, id).json()
    path = app.state.repo.path(a["id"])
    outside = tmp_path / "outside.json"
    outside.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(outside)
    assert client.get(f"/api/v1/artifacts/{a['id']}/content").status_code == 409


def test_reports_escape_untrusted_markup():
    from ghost_data.web.app import markdown_text

    text = markdown_text("<script>alert(1)</script> [click](javascript:alert(1))")
    assert "<script>" not in text and "\\[" in text
