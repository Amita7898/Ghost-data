"""Strict transport/domain contracts. Missing fields never imply compliant state."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, AwareDatetime, Field, StrictBool, StrictInt, model_validator

class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)

class Identifier(Model):
    kind: Literal['email', 'user_id', 'phone', 'hash']
    value: str = Field(min_length=1)

class Identity(Model):
    subject: str = Field(min_length=1)
    identifier: Identifier
    valid_from: AwareDatetime
    valid_to: AwareDatetime | None = None
    recorded_at: AwareDatetime

    @model_validator(mode='after')
    def interval(self):
        if self.valid_to and self.valid_to <= self.valid_from:
            raise ValueError('identity interval must be increasing')
        return self

class Resource(Model):
    system: str = Field(min_length=1)
    resource: str = Field(min_length=1)

    @property
    def key(self):
        return (self.system, self.resource)

class Rule(Model):
    category: str
    action: Literal['DELETE', 'RETAIN', 'REDACT', 'ANONYMIZE', 'DISABLE', 'BLOCK']
    required_fields: tuple[str, ...] = ()
    condition: str | None = None
    preserve_subject_reference: StrictBool = False

    @model_validator(mode='after')
    def requirements(self):
        if self.action in ('REDACT', 'ANONYMIZE') and not self.required_fields:
            raise ValueError('field treatment requires an explicit field inventory')
        return self

class Target(Resource):
    category: str
    conditions: dict[str, StrictBool] = {}
    depends_on: tuple[Resource, ...] = ()

class Observation(Resource):
    id: str = Field(min_length=1)
    identifier: Identifier
    observed_at: AwareDatetime
    captured_at: AwareDatetime
    event_at: AwareDatetime | None = None
    ingested_at: AwareDatetime | None = None
    available_at: AwareDatetime | None = None
    kind: Literal['CLAIM', 'READBACK']
    state: Literal['PRESENT', 'ABSENT', 'DISABLED', 'BLOCKED', 'ACTIVE', 'UNKNOWN']
    coverage: Literal['EXACT_RESOURCE', 'PARTIAL'] = 'PARTIAL'
    fields: dict[str, str | StrictInt | StrictBool | None] = {}
    unlinking_verified: StrictBool = False
    archive_present: StrictBool | None = None

    @model_validator(mode='before')
    @classmethod
    def legacy_times(cls, value):
        if not isinstance(value, dict):
            return value
        value = dict(value)
        fields = value.get('fields', {})
        for name in ('event_at', 'ingested_at'):
            if name in fields:
                if name in value and value[name] != fields[name]:
                    raise ValueError('Conflicting legacy and explicit timestamp')
                value[name] = fields[name]
        return value

    @model_validator(mode='after')
    def chronology(self):
        if self.captured_at < self.observed_at:
            raise ValueError('capture cannot precede observation')
        if self.event_at and self.event_at > self.observed_at:
            raise ValueError('event cannot follow observation')
        return self

class Request(Model):
    text: str
    identifier: Identifier
    requested_at: AwareDatetime
    audit_at: AwareDatetime
    evidence_cutoff: AwareDatetime | None = None
    require_ingestion_time: StrictBool = False

    @model_validator(mode='after')
    def chronology(self):
        if self.evidence_cutoff and self.evidence_cutoff > self.audit_at:
            raise ValueError('evidence cutoff cannot exceed audit cutoff')
        if self.audit_at < self.requested_at:
            raise ValueError('audit cannot precede request')
        return self

class Bundle(Model):
    schema_version: Literal[1] = 1
    request: Request
    identities: tuple[Identity, ...]
    rules: tuple[Rule, ...]
    targets: tuple[Target, ...]
    observations: tuple[Observation, ...]
    scope_complete: StrictBool = False

    @model_validator(mode='after')
    def uniqueness(self):
        for values in ([o.id for o in self.observations], [t.key for t in self.targets],
                       [r.category for r in self.rules]):
            if len(values) != len(set(values)):
                raise ValueError('duplicate observation, target, or rule')
        return self

class Assessment(Model):
    system: str
    resource: str
    status: Literal['SATISFIED', 'VIOLATED', 'UNRESOLVED']
    reason: str
    evidence: tuple[str, ...] = ()

class Report(Model):
    conclusion: Literal['VERIFIED_WITHIN_SCOPE', 'NON_COMPLIANT', 'INCONCLUSIVE', 'NOT_APPLICABLE']
    authorization: Literal['AUTHORIZED', 'DECLINED', 'NON_DELETION', 'AMBIGUOUS']
    subject: str | None
    artifact_sha256: str
    assessments: tuple[Assessment, ...]
    recommendations: tuple[dict, ...] = ()
    unresolved: tuple[str, ...] = ()
    validation_errors: tuple[str, ...] = ()
    provenance: dict[str, str] = {}
