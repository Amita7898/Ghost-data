"""Offline timeline playback. Provenance is a recording claim, not a signature."""

import json
from pathlib import Path

from ..models import Report


def save_trace(trace, path):
    path = Path(path)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(trace, stream, indent=2, ensure_ascii=False)


def replay(path):
    path = Path(path)
    if path.stat().st_size > 5_000_000:
        raise ValueError("Trace exceeds replay size limit")
    trace = json.loads(path.read_text())
    if trace.get("schema_version") != 1 or trace.get("execution") != "live_local":
        raise ValueError(
            "Replay requires a recorded live-local trace; test runtimes are not accepted"
        )
    events = trace.get("events", [])
    if [e.get("seq") for e in events] != list(range(1, len(events) + 1)):
        raise ValueError("Trace event sequence is invalid")
    if trace.get("status") == "verification_failed":
        errors = trace.get("validation_errors")
        if (
            trace.get("report") is not None
            or not isinstance(errors, list)
            or not errors
            or not all(isinstance(e, str) for e in errors)
        ):
            raise ValueError(
                "Verification-failed trace must withhold its report and record errors"
            )
        if (
            not events
            or events[-1].get("kind") != "verification_failed"
            or events[-1].get("data", {}).get("errors") != errors
        ):
            raise ValueError("Trace verification errors are inconsistent")
    else:
        Report.model_validate(trace["report"])
        if (
            not events
            or events[-1].get("kind") != "deterministic_conclusion"
            or events[-1]["data"].get("report") != trace["report"]
        ):
            raise ValueError("Trace final report is inconsistent")
    return {
        "mode": "OFFLINE_REPLAY",
        "recorded_model": trace["model"],
        "recorded_status": trace["status"],
        "events": events,
        "report": trace["report"],
        "validation_errors": trace.get("validation_errors", []),
    }
