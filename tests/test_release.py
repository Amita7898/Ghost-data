"""Release helpers stay offline and identify unsafe publication candidates."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts" / (name + ".py")
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_audit_rejects_private_paths_and_env_but_allows_example():
    m = module("release_audit")
    for path in (
        "dataset/test.json",
        ".env",
        ".env.production",
        ".localdata/web.sqlite",
        "log.txt",
    ):
        assert any(
            x["rule"] == "excluded_publication_path" for x in m.inspect(path, b"{}")
        )
    assert m.inspect(".env.example", b"# no secrets") == []


def test_audit_flags_tokens_without_returning_secret_values():
    m = module("release_audit")
    token = "sk-" + "x" * 40
    result = m.inspect("config.py", token.encode())
    assert result == [{"path": "config.py", "rule": "api_token"}]
    assert token not in str(result)


def test_audit_flags_machine_paths_without_logging_them():
    m = module("release_audit")
    value = "/" + "Users/" + "fixture/project"
    assert m.inspect("readme.md", value.encode()) == [
        {"path": "readme.md", "rule": "machine_home_path"}
    ]


def test_setup_is_offline_and_checks_all_curated_recordings(monkeypatch):
    m = module("check_setup")
    import urllib.request

    def forbidden(*args, **kwargs):
        raise AssertionError("Offline diagnostics contacted network")

    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    rows = m.checks()
    recordings = [r for r in rows if r[0].startswith("Recording ")]
    assert len(recordings) == 3 and all(r[1] for r in recordings)


def test_setup_detects_missing_recordings_and_ui(tmp_path):
    rows = module("check_setup").checks(tmp_path)
    assert ("Production UI", False) in [(name, ok) for name, ok, _ in rows]
    assert ("Demo recordings", False) in [(name, ok) for name, ok, _ in rows]


def test_conflict_demo_replays_genuine_rejections_without_runtime(tmp_path):
    from fastapi.testclient import TestClient

    from ghost_data.web.app import create_app

    def forbidden():
        raise AssertionError("Replay contacted runtime")

    with TestClient(
        create_app(ROOT, tmp_path / "data", runtime_factory=forbidden, offline=True),
        base_url="http://127.0.0.1",
    ) as client:
        response = client.post("/api/v1/demos/conflict/open")
        assert response.status_code == 201
        run = response.json()
        assert run["report"]["conclusion"] == "INCONCLUSIVE"
        events = client.get("/api/v1/runs/" + run["id"] + "/events").json()
        rejected = [
            e
            for e in events
            if e["kind"] == "hypothesis_validated"
            and e["data"]["result"]["accepted"] is False
        ]
        assert len(rejected) == 2
