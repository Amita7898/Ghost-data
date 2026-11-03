"""Application services: persistent progress and one admitted live run."""

import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ..agent.investigator import Investigator, Limits
from ..agent.replay import replay
from ..agent.runtime import Ollama
from ..evidence import load
from ..models import Bundle
from .models import CreateInvestigation
from .repository import elapsed, now

MAX_BYTES = 5_000_000
DEMO_FILES = {
    "receipt": (
        "Prose receipt audit",
        "A real five-turn investigation that validated a quoted readback.",
        "receipt-absent-v4-live.json",
        "prose_receipt.json",
    ),
    "replica": (
        "Remaining replica audit",
        "A real investigation of a remaining copy and its remediation.",
        "remaining-replica-v3-live.json",
        "remaining_replica.json",
    ),
}
EXAMPLES = {
    "receipt": "prose_receipt.json",
    "replica": "remaining_replica.json",
    "partial": "partial_snapshot.json",
    "claim": "claim_only.json",
}


class Service:
    def __init__(self, repo, root, runtime_factory=None):
        self.repo = repo
        self.root = Path(root)
        self.runtime_factory = runtime_factory or (lambda: Ollama(timeout=120))
        self.pool = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="ghost-investigation"
        )
        self.stopping = threading.Event()

    def shutdown(self):
        self.stopping.set()
        self.pool.shutdown(wait=False, cancel_futures=True)

    def parse(self, raw):
        path = self.repo.root / ("incoming-" + __import__("uuid").uuid4().hex + ".json")
        try:
            with path.open("xb") as f:
                f.write(raw)
            return load(path)
        finally:
            path.unlink(missing_ok=True)

    def configured(self, investigation, bundle):
        data = bundle.model_dump(mode="json")
        if investigation["audit_at"]:
            data["request"]["audit_at"] = investigation["audit_at"]
        if investigation["scope"] is not None:
            key = lambda t: json.dumps(
                [t["system"], t["resource"]], separators=(",", ":")
            )
            keys = {key(t) for t in data["targets"]}
            if not set(investigation["scope"]) <= keys:
                raise ValueError("Configured scope references unknown resources")
            if not investigation["scope"] and keys:
                raise ValueError("Select at least one resource")
            data["targets"] = [
                t for t in data["targets"] if key(t) in investigation["scope"]
            ]
        return Bundle.model_validate(data)

    def ingest(self, id, raw, filename, source="upload"):
        if len(raw) > MAX_BYTES:
            raise ValueError("Evidence exceeds 5 MB limit")
        bundle, _ = self.parse(raw)
        inv = self.repo.investigation(id)
        effective = self.configured(inv, bundle)
        configured = (
            json.dumps(effective.model_dump(mode="json"), sort_keys=True, indent=2)
            + "\n"
        ).encode()
        if effective != bundle and len(configured) > MAX_BYTES:
            raise ValueError("Configured bundle exceeds 5 MB limit")
        original = self.repo.store(id, raw, filename, source)
        if effective == bundle:
            return original
        return self.repo.store(id, configured, "configured-" + filename, "configured")

    def run_artifact(self, id, artifact):
        b, d = self.parse(self.repo.read(artifact["id"]))
        if d != artifact["sha256"]:
            raise ValueError("Evidence integrity check failed")
        effective = self.configured(self.repo.investigation(id), b)
        if b == effective:
            return artifact
        raw = (
            json.dumps(effective.model_dump(mode="json"), sort_keys=True, indent=2)
            + "\n"
        ).encode()
        digest = hashlib.sha256(raw).hexdigest()
        existing = next(
            (a for a in self.repo.artifacts(id) if a["sha256"] == digest), None
        )
        if existing:
            return existing
        if len(raw) > MAX_BYTES:
            raise ValueError("Configured bundle exceeds 5 MB limit")
        return self.repo.store(id, raw, "configured-input.json", "configured")

    def start(self, id, request, key):
        artifact = self.repo.artifact(request.artifact_id)
        if artifact["investigation_id"] != str(id):
            raise ValueError("Artifact belongs to another investigation")
        artifact = self.run_artifact(id, artifact)
        run, created = self.repo.start(
            id,
            artifact["id"],
            "live",
            "qwen3.5:latest",
            request.limits.model_dump(),
            key,
        )
        if created:
            self.repo.event(run["id"], {"kind": "run_queued", "data": {"mode": "live"}})
            self.pool.submit(self.worker, run["id"])
        return run

    def worker(self, id):
        repo = self.repo
        try:
            if self.stopping.is_set():
                raise RuntimeError("Backend stopping")
            if not repo.mark_running(id):
                repo.finish(id, status="cancelled", finished_at=now())
                return
            repo.event(id, {"kind": "run_started", "data": {"mode": "live"}})
            run = repo.run(id)
            runtime = self.runtime_factory()
            runtime.ready()
            repo.event(id, {"kind": "runtime_ready", "data": {"model": runtime.model}})
            bundle, digest = self.parse(repo.read(run["artifact_id"]))
            if digest != repo.artifact(run["artifact_id"])["sha256"]:
                raise ValueError("Evidence integrity check failed")
            offset = None

            def persist_agent_event(event):
                nonlocal offset
                if offset is None:
                    offset = elapsed(run["created_at"]) - event["elapsed_seconds"]
                repo.event(
                    id, {**event, "elapsed_seconds": event["elapsed_seconds"] + offset}
                )

            trace = Investigator(runtime, Limits.model_validate(run["limits"])).run(
                bundle,
                digest,
                cancel=lambda: (
                    self.stopping.is_set() or repo.run(id)["status"] == "cancelling"
                ),
                on_event=persist_agent_event,
            )
            status = trace["status"]
            if repo.run(id)["status"] == "cancelling" or self.stopping.is_set():
                status = "cancelled"
            final = (
                "completed"
                if status == "completed" and trace["execution"] == "live_local"
                else "cancelled"
                if status == "cancelled"
                else "failed"
            )
            repo.finish(
                id,
                status=final,
                finished_at=now(),
                report=trace["report"],
                conclusion=trace["report"]["conclusion"],
                usage=trace["usage"],
                trace=trace,
                error=None
                if final in ("completed", "cancelled")
                else "Investigation stopped: " + status,
            )
        except Exception as exc:  # noqa: BLE001 - worker boundary persists failures
            cancelled = repo.run(id)["status"] == "cancelling"
            message = (
                "Cancellation completed"
                if cancelled
                else "Local investigation unavailable or failed. Check Ollama with ghost-data doctor. ("
                + type(exc).__name__
                + ")"
            )
            repo.finish(
                id,
                status="cancelled" if cancelled else "failed",
                finished_at=now(),
                error=message,
            )

    def cancel(self, id):
        return self.repo.request_cancel(id)

    def demos(self):
        values = []
        for key, (title, description, trace_file, _) in DEMO_FILES.items():
            path = self.root / "demo" / trace_file
            if path.exists():
                trace = json.loads(path.read_text())
                values.append(
                    {
                        "id": key,
                        "title": title,
                        "description": description,
                        "model": trace["model"],
                        "turns": trace["usage"]["model_calls"],
                        "events": len(trace["events"]),
                    }
                )
        return values

    def open_demo(self, key):
        if key not in DEMO_FILES:
            raise KeyError("Unknown recorded demonstration")
        title, _, trace_file, bundle_file = DEMO_FILES[key]
        path = self.root / "demo" / trace_file
        manifest = json.loads((self.root / "demo/RECORDING_SHA256.json").read_text())
        if (
            hashlib.sha256(path.read_bytes()).hexdigest()
            != manifest["demo/" + trace_file]
        ):
            raise ValueError("Recording integrity check failed")
        replay(path)
        trace = json.loads(path.read_text())
        raw = (self.root / "examples" / bundle_file).read_bytes()
        if hashlib.sha256(raw).hexdigest() != trace["artifact_sha256"]:
            raise ValueError("Recording input mismatch")
        inv = self.repo.create(
            CreateInvestigation(title=title, subject_label="River · synthetic subject")
        )
        artifact = self.ingest(inv["id"], raw, bundle_file, "example")
        run, _ = self.repo.start(
            inv["id"], artifact["id"], "replay", trace["model"], trace["limits"]
        )
        for e in trace["events"]:
            self.repo.event(run["id"], e)
        self.repo.update(
            run["id"],
            status="completed",
            recorded_status=trace["status"],
            finished_at=now(),
            report=trace["report"],
            conclusion=trace["report"]["conclusion"],
            usage=trace["usage"],
            trace=trace,
        )
        return self.repo.run(run["id"])
