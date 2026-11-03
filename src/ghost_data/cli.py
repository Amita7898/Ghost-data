import argparse
import hashlib
import json
import sys
from pathlib import Path

from .agent.investigator import Investigator, Limits
from .agent.persistence import save_investigation
from .agent.replay import replay, save_trace
from .agent.runtime import Ollama, RuntimeFailure
from .engine import audit
from .evidence import load
from .storage import RunStore


def legacy_main() -> int:
    """Preserve the documented bundle-first CLI alongside agent subcommands."""
    parser = argparse.ArgumentParser(description="Ghost Data deterministic audit core")
    parser.add_argument("bundle", type=Path)
    parser.add_argument(
        "--db", type=Path, help="Optional local SQLite investigation history"
    )
    args = parser.parse_args()
    try:
        bundle, digest = load(args.bundle)
        report = audit(bundle, digest)
        if args.db:
            raw = args.bundle.read_bytes()

            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError("Artifact changed during investigation")
            run_id = RunStore(args.db).save(raw, report)
            print(f"Saved investigation {run_id}", file=sys.stderr)
        print(json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True))
        return 2 if report.validation_errors else 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"Audit failed: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    """Run offline audit/replay or explicitly selected local-model investigation."""
    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print(
            "Ghost Data: doctor | investigate BUNDLE --trace FILE | replay TRACE\nCompatibility: ghost-data BUNDLE [--db FILE]\nUse a subcommand with --help for its options."
        )
        return 0
    if len(sys.argv) < 2 or sys.argv[1] not in ("doctor", "investigate", "replay"):
        return legacy_main()

    parser = argparse.ArgumentParser(description="Ghost Data local investigation agent")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--model", default="qwen3.5:latest")
    inv = sub.add_parser("investigate")
    inv.add_argument("bundle", type=Path)
    inv.add_argument("--agent", choices=["local"], default="local")
    inv.add_argument("--model", default="qwen3.5:latest")
    inv.add_argument("--trace", type=Path, required=True)
    inv.add_argument("--turns", type=int, default=6)
    inv.add_argument("--context", type=int, default=16384)
    inv.add_argument("--seconds", type=int, default=300)
    inv.add_argument("--db", type=Path)
    inv.add_argument("--tool-calls", type=int, default=24)
    inv.add_argument("--tokens", type=int, default=64000)
    inv.add_argument("--output-tokens", type=int, default=512)
    inv.add_argument("--timeout", type=int, default=120)
    rep = sub.add_parser("replay")
    rep.add_argument("trace", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "replay":
            print(json.dumps(replay(args.trace), indent=2))
            return 0
        runtime = Ollama(
            model=args.model,
            timeout=args.timeout if args.command == "investigate" else 120,
        )
        readiness = runtime.ready()
        if args.command == "doctor":
            print(json.dumps(readiness, indent=2))
            return 0
        if args.trace.exists():
            raise ValueError("Trace path already exists")
        bundle, digest = load(args.bundle)
        raw = args.bundle.read_bytes()

        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("Artifact changed before investigation")
        trace = Investigator(
            runtime,
            Limits(
                turns=args.turns,
                context=args.context,
                seconds=args.seconds,
                tools=args.tool_calls,
                tokens=args.tokens,
                output=args.output_tokens,
            ),
        ).run(
            bundle,
            digest,
            on_event=lambda e: print(f"{e['seq']}: {e['kind']}", file=sys.stderr),
        )
        trace["runtime_readiness"] = readiness
        save_trace(trace, args.trace)
        if args.db:
            save_investigation(args.db, raw, trace)
        print(
            json.dumps(
                {
                    "status": trace["status"],
                    "report": trace["report"],
                    "usage": trace["usage"],
                    "trace": str(args.trace),
                },
                indent=2,
            )
        )
        return 0 if trace["status"] == "completed" else 2
    except KeyboardInterrupt:
        print("Investigation interrupted", file=sys.stderr)
        return 130
    except (RuntimeFailure, ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
