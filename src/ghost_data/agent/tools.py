"""Typed bounded tools. Objects come only from the registered visible bundle."""

import json
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..engine import audit
from ..evidence import eligible, provenance
from ..identity import normalized, resolve, subject_for_request
from ..models import Bundle, Identifier, Observation
from .interpretation import interpret


def content_values(value):
    """Yield searchable values, never serialization/schema field names."""
    if isinstance(value, dict):
        for item in value.values():
            yield from content_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from content_values(item)
    elif value is not None:
        yield str(value).casefold()


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ContextArgs(Args):
    pass


class SearchArgs(Args):
    query: str = Field(default="", max_length=120)
    offset: int = Field(default=0, ge=0, le=10000)


class ReadArgs(Args):
    evidence_id: str = Field(min_length=1, max_length=120)


class IdentityArgs(Args):
    kind: Literal["email", "user_id", "phone", "hash"]
    value: str = Field(min_length=1, max_length=200)


class HistoryArgs(Args):
    system: str = Field(min_length=1, max_length=120)
    resource: str = Field(min_length=1, max_length=120)


class ProposalArgs(HistoryArgs):
    evidence_id: str = Field(min_length=1, max_length=120)
    claim: Literal["STATE", "IDENTITY", "RELATIONSHIP"]
    value: str = Field(min_length=1, max_length=200)
    quote: str = Field(
        default="",
        max_length=1000,
        description="For a resource_readback_note, copy the exact Resource ... Observed state: ... sentence from note. Otherwise use empty string.",
    )


DEFINITIONS = {
    "get_context": (
        ContextArgs,
        "Get trusted scope, unresolved obligations and resource identifiers; no evidence text.",
    ),
    "search_evidence": (
        SearchArgs,
        "Search eligible subject-linked observations matching ANY query token. Query may be empty. Paginate 8 at a time.",
    ),
    "read_evidence": (
        ReadArgs,
        "Read one registered eligible observation and its exact source locator.",
    ),
    "resolve_identity": (
        IdentityArgs,
        "Resolve a typed identifier through registered current and historical identity rows.",
    ),
    "inspect_resource": (
        HistoryArgs,
        "Inspect eligible history, readback/claim type and snapshot coverage for one scoped resource.",
    ),
    "submit_hypothesis": (
        ProposalArgs,
        "Validate a STATE value or IDENTITY subject against cited source. RELATIONSHIP uses an explicit system/resource dependency key. For prose READBACK notes, supply the exact source sentence in quote; the source contract must support it. Rejected hypotheses must not be reported as facts.",
    ),
}


def schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": desc,
                "parameters": cls.model_json_schema(),
            },
        }
        for name, (cls, desc) in DEFINITIONS.items()
    ]


class Tools:
    def __init__(self, bundle: Bundle, digest: str) -> None:
        self.bundle = bundle
        self.digest = digest
        self.subject = subject_for_request(bundle)
        self.report = audit(bundle, digest)
        self.sources = provenance(bundle, digest)
        self.accepted = []
        self.rejected = []
        self.calls = 0
        self.read_sources: set[str] = set()

    def observations(self) -> list[Observation]:
        if not self.subject or self.report.authorization != "AUTHORIZED":
            return []
        return [
            o
            for t in self.bundle.targets
            for o in eligible(self.bundle, t, self.subject)
        ]

    def execute(self, name: str, args: dict) -> dict:
        """Validate one bounded call, then dispatch without granting new capabilities."""
        self.calls += 1
        if name not in DEFINITIONS:
            return {"error": "Unknown tool"}
        try:
            arg = DEFINITIONS[name][0].model_validate(args)
        except ValueError:
            return {"error": "Invalid typed tool arguments"}
        handlers = {
            "get_context": self._get_context,
            "search_evidence": self._search_evidence,
            "read_evidence": self._read_evidence,
            "resolve_identity": self._resolve_identity,
            "inspect_resource": self._inspect_resource,
            "submit_hypothesis": self._submit_hypothesis,
        }
        result = handlers[name](arg)
        # Never crop JSON or silently discard evidence qualifiers.
        if len(json.dumps(result)) > 6000:
            return {"error": "Result too large; narrow the query or source fragment"}
        return result

    def _get_context(self, arg: ContextArgs) -> dict:
        b = self.bundle
        result = {
            "request": b.request.model_dump(mode="json"),
            "subject": self.subject,
            "authorization": self.report.authorization,
            "policies": [r.model_dump(mode="json") for r in b.rules[:20]],
            "targets": [t.model_dump(mode="json") for t in b.targets[:20]],
            "targets_truncated": len(b.targets) > 20,
            "unresolved": list(self.report.unresolved)[:20],
            "instruction": "Inspect evidence with tools; conclusions are issued by the deterministic kernel.",
        }
        return result

    def _search_evidence(self, arg: SearchArgs) -> dict:
        obs = self.observations()
        terms = re.findall("[\\w@.+:-]+", arg.query.casefold())
        matches = [
            o
            for o in obs
            if not terms
            or any(
                term in " ".join(content_values(o.model_dump(mode="json")))
                for term in terms
            )
        ]
        result = {
            "total": len(matches),
            "offset": arg.offset,
            "items": [
                {
                    "id": o.id,
                    "system": o.system,
                    "resource": o.resource,
                    "kind": o.kind,
                    "source": self.sources[o.id],
                }
                for o in matches[arg.offset : arg.offset + 8]
            ],
        }
        return result

    def _read_evidence(self, arg: ReadArgs) -> dict:
        obs = self.observations()
        o = next(
            (
                o
                for o in obs
                if o.id == arg.evidence_id or self.sources[o.id] == arg.evidence_id
            ),
            None,
        )
        result = (
            {
                "evidence_id": o.id,
                "observation": o.model_dump(mode="json"),
                "source": self.sources[o.id],
            }
            if o
            else {"error": "Evidence not in eligible subject scope"}
        )
        if o and len(json.dumps(result)) <= 6000:
            self.read_sources.add(o.id)
        return result

    def _resolve_identity(self, arg: IdentityArgs) -> dict:
        if self.report.authorization != "AUTHORIZED":
            return {"error": "Identity investigation is not authorized"}
        b = self.bundle
        ident = Identifier(kind=arg.kind, value=arg.value)
        if not self.subject or not any(
            normalized(i.identifier) == normalized(ident)
            and i.subject == self.subject
            and (i.recorded_at <= b.request.audit_at)
            for i in b.identities
        ):
            result = {"error": "Identifier outside subject scope"}
        else:
            matched = [
                (n, i)
                for n, i in enumerate(b.identities)
                if normalized(i.identifier) == normalized(ident)
                and i.recorded_at <= b.request.audit_at
            ]
            ambiguous = len({i.subject for _, i in matched}) != 1
            rows = (
                [(n, i) for n, i in matched if i.subject == self.subject]
                if ambiguous
                else [
                    (n, i)
                    for n, i in enumerate(b.identities)
                    if i.subject == self.subject and i.recorded_at <= b.request.audit_at
                ]
            )
            result = {
                "history_truncated": len(rows) > 10,
                "rows": [
                    {
                        "identity": i.model_dump(mode="json"),
                        "source": self.sources[f"identities:{n}"],
                    }
                    for n, i in rows[:10]
                ],
                "ambiguous": ambiguous,
            }
        return result

    def _inspect_resource(self, arg: HistoryArgs) -> dict:
        b = self.bundle
        obs = self.observations()
        target = next(
            (t for t in b.targets if t.key == (arg.system, arg.resource)), None
        )
        rows = [o for o in obs if o.key == (arg.system, arg.resource)]
        result = (
            {
                "target": target.model_dump(mode="json"),
                "history": [
                    {
                        "id": o.id,
                        "state": o.state,
                        "kind": o.kind,
                        "coverage": o.coverage,
                        "observed_at": o.observed_at.isoformat(),
                        "source": self.sources[o.id],
                    }
                    for o in rows[:10]
                ],
            }
            if target
            else {"error": "Resource outside scope"}
        )
        return result

    def _submit_hypothesis(self, arg: ProposalArgs) -> dict:
        b = self.bundle
        obs = self.observations()
        o = next(
            (
                o
                for o in obs
                if (o.id == arg.evidence_id or self.sources[o.id] == arg.evidence_id)
                and o.key == (arg.system, arg.resource)
            ),
            None,
        )
        before_bundle = self.bundle
        before_report = self.report
        supported = False
        reason = "Citation does not support claim"
        if o and arg.claim == "STATE" and arg.quote:
            derived = interpret(o, self.subject, arg.quote, arg.value)
            if derived:
                self.bundle = self.bundle.model_copy(
                    update={
                        "observations": tuple(
                            derived if x.id == o.id else x
                            for x in self.bundle.observations
                        )
                    }
                )
                self.report = audit(self.bundle, self.digest)
                o = derived
        if o:
            if arg.claim == "STATE":
                target_assessment = next(
                    (
                        a
                        for a in self.report.assessments
                        if (a.system, a.resource) == o.key
                    ),
                    None,
                )
                supported = (
                    o.kind == "READBACK"
                    and o.observed_at == b.request.audit_at
                    and (o.state == arg.value)
                    and (o.state != "ABSENT" or o.coverage == "EXACT_RESOURCE")
                    and (target_assessment is not None)
                    and (target_assessment.status != "UNRESOLVED")
                )
            elif arg.claim == "IDENTITY":
                supported = arg.value == self.subject and resolve(
                    o.identifier, o.observed_at, b.request.audit_at, b.identities
                ) == {self.subject}
            else:
                target = next((t for t in b.targets if t.key == o.key), None)
                supported = bool(
                    target
                    and any(
                        f"{d.system}/{d.resource}" == arg.value
                        for d in target.depends_on
                    )
                    and (o.fields.get("depends_on") == arg.value)
                )
        if not supported:
            self.bundle = before_bundle
            self.report = before_report
        result = {
            "accepted": bool(supported),
            "proposal": arg.model_dump(),
            "reason": "Supported by registered source and proof rules"
            if supported
            else reason,
            "source": self.sources[o.id] if o else None,
        }
        if len(json.dumps(result)) <= 6000:
            (self.accepted if supported else self.rejected).append(result)
        return result

    def review_follow_up(self, proposal: dict) -> dict:
        """Validate advisory question scope/citations, never the question's truth."""
        key = (proposal["system"], proposal["resource"])
        assessment = next(
            (a for a in self.report.assessments if (a.system, a.resource) == key), None
        )
        rows = {o.id: o for o in self.observations() if o.key == key}
        ids = proposal["evidence_ids"]
        reason = None
        if assessment is None or assessment.status != "UNRESOLVED":
            reason = (
                "Questions must concern an unresolved resource in the authorized scope"
            )
        elif any(id not in rows or id not in self.read_sources for id in ids):
            reason = (
                "Citations must be eligible evidence actually read for this resource"
            )
        elif rows and not ids:
            reason = (
                "Available evidence must be read and cited before proposing a follow-up"
            )
        return {
            "linked": reason is None,
            "advisory_only": True,
            "proposal": proposal,
            "reason": reason
            or "Scope and citations checked; question remains unverified model content",
            "sources": [
                self.sources[id] for id in ids if id in rows and id in self.read_sources
            ],
        }
