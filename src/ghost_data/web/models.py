from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from ..agent.investigator import Limits
from ..models import Bundle, Report

Status = Literal[
    "queued", "running", "cancelling", "completed", "cancelled", "failed", "interrupted"
]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateInvestigation(Model):
    title: str = Field(min_length=1, max_length=100)
    subject_label: str = Field(default="", max_length=160)
    audit_at: AwareDatetime | None = None
    scope: list[str] | None = Field(default=None, max_length=100)


class Investigation(Model):
    id: UUID
    title: str
    subject_label: str
    audit_at: str | None
    scope: list[str] | None
    created_at: str
    latest_run: dict | None = None
    evidence_count: int = 0


class Artifact(Model):
    id: UUID
    investigation_id: UUID
    filename: str
    sha256: str
    size: int
    source: Literal["upload", "example", "configured"]
    created_at: str


class StartRun(Model):
    artifact_id: UUID
    limits: Limits = Field(default_factory=Limits)


class Run(Model):
    id: UUID
    investigation_id: UUID
    artifact_id: UUID
    mode: Literal["live", "replay"]
    status: Status
    recorded_status: str | None = None
    created_at: str
    finished_at: str | None = None
    conclusion: str | None = None
    error: str | None = None
    model: str
    usage: dict | None = None
    report: Report | None = None
    limits: dict


class Event(Model):
    seq: int
    elapsed_seconds: float
    kind: str
    data: dict


class Error(Model):
    code: str
    message: str
    details: list[dict] = Field(default_factory=list)


class Relationship(Model):
    from_: str = Field(alias="from")
    to: str
    label: str
    evidence_id: str
    source: str


class Context(Model):
    investigation: Investigation
    bundle: Bundle | None
    artifact: Artifact | None = None
    subject: str | None = None
    relationships: list[Relationship] = Field(default_factory=list)
    eligibility: dict[str, list[str]] = Field(default_factory=dict)


class Demo(Model):
    id: str
    title: str
    description: str
    model: str
    turns: int
    events: int


class RuntimeStatus(Model):
    available: bool
    model: str
    message: str


class Preview(Model):
    source: str
    text: str
    truncated: bool
