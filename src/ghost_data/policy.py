"""Policy assessment deliberately distinguishes absent from omitted fields."""

from .evidence import eligible
from .models import Assessment, Bundle, Observation, Rule, Target


def assess(bundle: Bundle, target: Target, subject: str) -> Assessment:
    """Evaluate all eligible cutoff readbacks; conflicts remain unresolved."""

    def result(status, reason, observations=()):
        return Assessment(
            system=target.system,
            resource=target.resource,
            status=status,
            reason=reason,
            evidence=tuple(o.id for o in observations),
        )

    rule = next((r for r in bundle.rules if r.category == target.category), None)
    if rule is None:
        return result("UNRESOLVED", "No applicable policy")
    if rule.condition and target.conditions.get(rule.condition) is not True:
        return result(
            "UNRESOLVED", "Policy condition missing or false; fallback policy required"
        )
    obs = [
        o
        for o in eligible(bundle, target, subject)
        if o.kind == "READBACK" and o.observed_at == bundle.request.audit_at
    ]
    if not obs:
        return result(
            "UNRESOLVED", "No subject-attributed readback at the audit cutoff"
        )
    states = [evaluate(rule, o, subject) for o in obs]
    if len(set(states)) != 1:
        return result("UNRESOLVED", "Conflicting or incomplete readbacks", obs)
    state = states[0]
    return result(
        state,
        {
            "SATISFIED": "Required treatment observed",
            "VIOLATED": "Policy violation observed",
            "UNRESOLVED": "Insufficient fields or coverage",
        }[state],
        obs,
    )


def evaluate(rule: Rule, o: Observation, subject: str) -> str:
    """Classify one observation without treating missing fields as redacted."""
    if o.state == "UNKNOWN":
        return "UNRESOLVED"
    if rule.action in ("REDACT", "ANONYMIZE"):
        if o.state == "ABSENT":
            return "VIOLATED" if o.coverage == "EXACT_RESOURCE" else "UNRESOLVED"
        if o.state != "PRESENT":
            return "UNRESOLVED"
        if any(o.fields.get(f) not in (None, "") for f in rule.required_fields):
            return "VIOLATED"
        if not all(f in o.fields for f in rule.required_fields):
            return "UNRESOLVED"
        if (
            rule.preserve_subject_reference
            and o.fields.get("subject_reference") != subject
        ):
            return "UNRESOLVED"
        if rule.action == "ANONYMIZE" and not o.unlinking_verified:
            return "UNRESOLVED"
        return "SATISFIED"
    desired = {
        "DELETE": "ABSENT",
        "RETAIN": "PRESENT",
        "DISABLE": "DISABLED",
        "BLOCK": "BLOCKED",
    }[rule.action]
    if o.state == "ABSENT" and o.coverage != "EXACT_RESOURCE":
        return "UNRESOLVED"
    if rule.action == "BLOCK" and o.archive_present is not True:
        return "UNRESOLVED"
    valid = {
        "DELETE": {"PRESENT", "ABSENT"},
        "RETAIN": {"PRESENT", "ABSENT"},
        "DISABLE": {"ACTIVE", "DISABLED"},
        "BLOCK": {"ACTIVE", "BLOCKED"},
    }[rule.action]
    if o.state not in valid:
        return "UNRESOLVED"
    return "SATISFIED" if o.state == desired else "VIOLATED"
