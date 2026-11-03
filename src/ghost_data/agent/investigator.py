"""Bounded model-driven tool loop. Final authority stays in the kernel/verifier."""

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from importlib.resources import files
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..models import Bundle
from ..verifier import check
from .runtime import RuntimeFailure
from .tools import DEFINITIONS, Tools, schemas

PROMPT_VERSION = "investigator-v5"
SYSTEM = (
    files("ghost_data.agent")
    .joinpath("prompts/investigator-v5.txt")
    .read_text(encoding="utf-8")
    .removesuffix("\n")
)


class FollowUp(BaseModel):
    """Untrusted advisory model output with bounded, host-checked references."""

    model_config = ConfigDict(extra="forbid", strict=True)
    system: str = Field(min_length=1, max_length=120)
    resource: str = Field(min_length=1, max_length=120)
    question: str = Field(min_length=1, max_length=240)
    evidence_ids: list[Annotated[str, Field(min_length=1, max_length=120)]] = Field(
        max_length=5
    )


class Completion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str = Field(max_length=500)
    uncertainties: list[Annotated[str, Field(max_length=150)]] = Field(max_length=5)
    stop_reason: Literal["resolved", "insufficient_evidence"]
    follow_ups: list[FollowUp] = Field(default_factory=list, max_length=3)


class Limits(BaseModel):
    model_config = ConfigDict(extra="forbid")
    turns: int = Field(default=6, ge=1, le=40)
    tools: int = Field(default=24, ge=1, le=100)
    tokens: int = Field(default=64000, ge=128, le=100000)
    context: int = Field(default=16384, ge=2048, le=32768)
    output: int = Field(default=512, ge=64, le=2048)
    seconds: int = Field(default=300, ge=1, le=1800)


class Investigator:
    def __init__(self, runtime, limits=None):
        self.runtime = runtime
        self.limits = limits or Limits()

    def run(
        self,
        bundle: Bundle,
        digest: str,
        goal: str = "Investigate deletion compliance, source ownership, contradictions and missing proof.",
        cancel: Callable[[], bool] | None = None,
        on_event: Callable[[dict], None] | None = None,
    ) -> dict:
        """Investigate with bounded tools; return a journal even if proof fails."""
        limits = self.limits
        tools = Tools(bundle, digest)
        started = time.monotonic()
        events = []
        trace = {
            "schema_version": 1,
            "investigation_id": str(uuid.uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "execution": "live_local" if self.runtime.live else "test_runtime",
            "model": self.runtime.model,
            "prompt_version": PROMPT_VERSION,
            "tool_schema_version": 2,
            "limits": limits.model_dump(),
            "prompt_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
            "tool_schema_sha256": hashlib.sha256(
                json.dumps(schemas(), sort_keys=True).encode()
            ).hexdigest(),
            "generation": {
                "temperature": 0,
                "presence_penalty": 0,
                "seed": 42,
                "think": False,
            },
            "artifact_sha256": digest,
            "events": events,
            "usage": {"model_calls": 0, "input_tokens": 0, "output_tokens": 0},
            "status": "running",
        }

        def event(kind, data):
            item = {
                "seq": len(events) + 1,
                "elapsed_seconds": time.monotonic() - started,
                "kind": kind,
                "data": json.loads(json.dumps(data)),
            }
            events.append(item)
            if on_event:
                on_event(json.loads(json.dumps(item)))

        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": "Investigation goal: " + goal[:1000]},
        ]
        event("investigation_started", {"goal": goal[:1000]})
        status = "turn_budget_exhausted"
        completion = None
        for turn in range(limits.turns):
            if cancel and cancel():
                status = "cancelled"
                break
            remaining = limits.seconds - (time.monotonic() - started)
            if remaining <= 0:
                status = "time_budget_exhausted"
                break
            # Conservative UTF-8 byte bound: at most one token per byte for supported tokenizers.
            budget_bytes = len(json.dumps(messages, ensure_ascii=False).encode()) + len(
                json.dumps(schemas()).encode()
            )
            if (
                budget_bytes + limits.output > limits.context
                or trace["usage"]["input_tokens"]
                + trace["usage"]["output_tokens"]
                + budget_bytes
                + limits.output
                > limits.tokens
            ):
                status = "context_or_token_budget_exhausted"
                break
            event("model_requested", {"turn": turn + 1})
            trace["usage"]["model_calls"] += 1
            try:
                if hasattr(self.runtime, "timeout"):
                    self.runtime.timeout = min(self.runtime.timeout, remaining)
                finishing = turn >= max(0, limits.turns - 2)
                request_messages = messages + (
                    [
                        {
                            "role": "user",
                            "content": "This is the final budgeted turn. Return the required JSON summary, uncertainties and stop_reason; no further tools are available.",
                        }
                    ]
                    if finishing
                    else []
                )
                result = self.runtime.chat(
                    request_messages,
                    [] if finishing else schemas(),
                    context=limits.context,
                    predict=limits.output,
                    format=Completion.model_json_schema() if finishing else None,
                )
                message = result["message"]
                if message.get("role") != "assistant":
                    raise RuntimeFailure("Invalid assistant role")
                calls = message.get("tool_calls", [])
                if not isinstance(calls, list):
                    raise RuntimeFailure("Invalid tool-call response")
            except KeyboardInterrupt:
                status = "cancelled"
                event("error", {"type": "KeyboardInterrupt"})
                break
            except (RuntimeFailure, KeyError, ValueError, TypeError) as exc:
                status = (
                    "time_budget_exhausted"
                    if time.monotonic() - started >= limits.seconds
                    else "inference_failed"
                )
                event(
                    "error",
                    {
                        "type": type(exc).__name__,
                        "message": str(exc)
                        if isinstance(exc, RuntimeFailure)
                        else "Invalid runtime message",
                    },
                )
                break
            trace["usage"]["input_tokens"] += result.get("prompt_eval_count", 0)
            trace["usage"]["output_tokens"] += result.get("eval_count", 0)
            event(
                "model_completed",
                {
                    "turn": turn + 1,
                    "prompt_tokens": result.get("prompt_eval_count"),
                    "output_tokens": result.get("eval_count"),
                    "eval_duration_ns": result.get("eval_duration"),
                    "total_duration_ns": result.get("total_duration"),
                    "done_reason": result.get("done_reason"),
                    "tool_call_count": len(calls),
                },
            )
            if (
                trace["usage"]["input_tokens"] + trace["usage"]["output_tokens"]
                > limits.tokens
            ):
                status = "token_budget_exhausted"
                break
            # Never retain a runtime's separate thinking field.
            messages.append(
                {
                    "role": "assistant",
                    "content": message.get("content", ""),
                    "tool_calls": calls,
                }
            )
            if calls:
                for call in calls:
                    if cancel and cancel():
                        status = "cancelled"
                        break
                    if tools.calls >= limits.tools:
                        status = "tool_budget_exhausted"
                        break
                    fn = call.get("function", {}) if isinstance(call, dict) else {}
                    if not isinstance(fn, dict):
                        fn = {}
                    name = fn.get("name")
                    args = fn.get("arguments", {})
                    if not isinstance(name, str) or not isinstance(args, dict):
                        status = "malformed_tool_call"
                        event("error", {"type": "MalformedToolCall"})
                        break
                    # Logging arguments follows schema validation; do not persist arbitrary payloads.
                    try:
                        validated = (
                            DEFINITIONS[name][0].model_validate(args).model_dump()
                        )
                    except (KeyError, ValueError):
                        validated = None
                    event("tool_requested", {"name": name, "arguments": validated})
                    value = tools.execute(name, args)
                    event(
                        "hypothesis_validated"
                        if name == "submit_hypothesis"
                        else "tool_returned",
                        {"name": name, "result": value},
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": name,
                            "content": json.dumps({"untrusted_tool_data": value}),
                        }
                    )
                    if (
                        name == "read_evidence"
                        and "observation" in value
                        and not tools.accepted
                    ):
                        messages.append(
                            {
                                "role": "user",
                                "content": "The source has been retrieved. Assess whether it supports a hypothesis and submit it for validation, or identify the unresolved gap. Avoid redundant searches.",
                            }
                        )
                if status in (
                    "tool_budget_exhausted",
                    "cancelled",
                    "malformed_tool_call",
                ):
                    break
            else:
                try:
                    completion = Completion.model_validate_json(
                        message.get("content", "")
                    )
                except ValueError as exc:
                    details = (
                        [
                            {"type": e["type"], "location": list(e["loc"])}
                            for e in exc.errors(include_input=False)
                        ][:10]
                        if hasattr(exc, "errors")
                        else []
                    )
                    event(
                        "completion_rejected",
                        {"reason": "Invalid final JSON schema", "errors": details},
                    )
                    messages.append(
                        {
                            "role": "user",
                            "content": "Return final JSON matching the required summary, uncertainties, stop_reason schema, or use a tool.",
                        }
                    )
                    continue
                event("model_summary", completion.model_dump())
                for proposal in completion.follow_ups:
                    event(
                        "follow_up_proposed",
                        tools.review_follow_up(proposal.model_dump()),
                    )
                status = "completed"
                break
        report = tools.report
        try:
            errors = check(tools.bundle, report)
        except (
            Exception
        ) as exc:  # Fail closed while preserving the investigation journal.
            errors = [f"Independent verifier could not complete ({type(exc).__name__})"]
        errors = list(dict.fromkeys([*report.validation_errors, *errors]))
        if errors:
            status = "verification_failed"
        trace.update(
            status=status,
            duration_seconds=time.monotonic() - started,
            tool_calls=tools.calls,
            accepted=tools.accepted,
            rejected=tools.rejected,
            completion=completion.model_dump() if completion else None,
            report=None if errors else report.model_dump(mode="json"),
            validation_errors=errors,
        )
        if errors:
            event(
                "verification_failed",
                {
                    "message": "Independent evidence verification rejected the assessment; no audit conclusion published.",
                    "errors": errors,
                },
            )
        else:
            event(
                "deterministic_conclusion",
                {"report": trace["report"], "execution_status": status},
            )
        return trace
