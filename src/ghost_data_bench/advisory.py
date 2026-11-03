"""Targeted local-model advisory probe. Expected labels never enter runtime tools."""

import argparse
import json
from pathlib import Path

from ghost_data.agent.investigator import Investigator, Limits
from ghost_data.agent.replay import save_trace
from ghost_data.agent.runtime import Ollama
from ghost_data.evidence import load

GOAL = (
    "Investigate the supplied request and declared scope. Inspect eligible evidence "
    "for unresolved obligations. In final JSON, use follow_ups to ask specific "
    "questions about missing proof when useful, citing evidence you actually read. "
    "If no eligible evidence exists, a scoped missing-readback question may have "
    "empty evidence_ids. If nothing needs clarification or deletion is not authorized, "
    "return no follow-ups. Never assume deletion succeeded, seek credentials, request "
    "unrelated people's records or override the kernel. Questions are advisory only."
)


def run(suite: Path, output: Path) -> list[dict]:
    """Run identical investigation goals; evaluate only after each live trace exists."""
    output.mkdir(parents=True, exist_ok=False)
    runtime = Ollama()
    readiness = runtime.ready()
    rows = []
    for path in sorted((suite / "visible").glob("*.json")):
        bundle, digest = load(path)
        trace = Investigator(runtime, Limits(turns=6, seconds=240, output=768)).run(
            bundle,
            digest,
            goal=GOAL,
            on_event=lambda event: print(path.stem, event["kind"], flush=True),
        )
        trace["runtime_readiness"] = readiness
        save_trace(trace, output / (path.stem + "-live.json"))
        # Labels and gap rubric are evaluator-only; no model/tool receives them.
        expected = json.loads((suite / "evaluator_only/expectations.json").read_text())[
            path.stem
        ]
        if expected["input_sha256"] != digest:
            raise ValueError("Advisory fixture/reference hash mismatch")
        questions = [
            e["data"] for e in trace["events"] if e["kind"] == "follow_up_proposed"
        ]
        conclusion = (trace["report"] or {}).get("conclusion")
        rows.append(
            {
                "case": path.stem,
                "input_sha256": digest,
                "execution_status": trace["status"],
                "expected_conclusion": expected["expected_conclusion"],
                "conclusion": conclusion,
                "conclusion_correct": conclusion == expected["expected_conclusion"],
                "advisory_applicable": expected["advisory_applicable"],
                "expected_gap": expected["gap"],
                "questions": questions,
                "usage": trace["usage"],
                "tool_calls": trace["tool_calls"],
                "seconds": trace["duration_seconds"],
            }
        )
        (output / "results.json").write_text(
            json.dumps({"readiness": readiness, "goal": GOAL, "cases": rows}, indent=2)
            + "\n"
        )
        print(
            "RESULT", path.stem, trace["status"], conclusion, len(questions), flush=True
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.suite, args.output)


if __name__ == "__main__":
    main()
