"""Independent proof checker: deliberately does not import policy assessment code."""

from .authorization import classify
from .evidence import eligible
from .identity import subject_for_request
from .models import Bundle, Report


def check(bundle: Bundle, report: Report) -> list[str]:
    """Check evidence and policy directly without trusting assessment reasons."""
    errors = []
    auth = classify(bundle.request.text)
    subject = subject_for_request(bundle)
    if report.authorization != auth or report.subject != subject:
        errors.append("Authorization or subject mismatch")
    if auth != "AUTHORIZED":
        expected = (
            "NOT_APPLICABLE" if auth in ("DECLINED", "NON_DELETION") else "INCONCLUSIVE"
        )
        if (
            report.conclusion != expected
            or report.assessments
            or report.recommendations
        ):
            errors.append(
                "Unauthorized or ambiguous request cannot produce an action plan"
            )
        return errors
    targets = {t.key: t for t in bundle.targets}
    assessments = {(a.system, a.resource): a for a in report.assessments}
    if set(targets) != set(assessments) or len(assessments) != len(report.assessments):
        errors.append("Obligation inventory mismatch")
    obs = {o.id: o for o in bundle.observations}
    cutoff = bundle.request.audit_at
    for key, a in assessments.items():
        if key not in targets:
            continue
        target = targets[key]
        rule = next((r for r in bundle.rules if r.category == target.category), None)
        if a.status == "UNRESOLVED":
            continue
        if (
            subject is None
            or rule is None
            or (rule.condition and target.conditions.get(rule.condition) is not True)
        ):
            errors.append(f"{key}: unsupported subject or policy")
            continue
        usable = [
            o
            for o in eligible(bundle, target, subject)
            if o.kind == "READBACK" and o.observed_at == cutoff
        ]
        if not usable or set(a.evidence) != {o.id for o in usable}:
            errors.append(f"{key}: missing, invented or selectively omitted evidence")
            continue
        for evidence_id in a.evidence:
            o = obs[evidence_id]
            proof = None
            if rule.action in ("DELETE", "RETAIN"):
                if o.state == "PRESENT":
                    proof = rule.action == "RETAIN"
                elif o.state == "ABSENT" and o.coverage == "EXACT_RESOURCE":
                    proof = rule.action == "DELETE"
            elif rule.action in ("DISABLE", "BLOCK"):
                if rule.action != "BLOCK" or o.archive_present is True:
                    final = "DISABLED" if rule.action == "DISABLE" else "BLOCKED"
                    if o.state in ("ACTIVE", final):
                        proof = o.state == final
            elif rule.action in ("REDACT", "ANONYMIZE"):
                if o.state == "ABSENT" and o.coverage == "EXACT_RESOURCE":
                    proof = False
                elif o.state == "PRESENT":
                    if any(
                        f in o.fields and o.fields[f] not in (None, "")
                        for f in rule.required_fields
                    ):
                        proof = False
                    elif (
                        set(rule.required_fields) <= set(o.fields)
                        and (
                            not rule.preserve_subject_reference
                            or o.fields.get("subject_reference") == subject
                        )
                        and (rule.action != "ANONYMIZE" or o.unlinking_verified)
                    ):
                        proof = True
            if proof is None or (a.status == "SATISFIED") != proof:
                errors.append(f"{key}: evidence does not establish {a.status}")
    seen = set()
    for rec in report.recommendations:
        key = (rec.get("system"), rec.get("resource"))
        target = targets.get(key)
        rule = next(
            (r for r in bundle.rules if target and r.category == target.category), None
        )
        assessment = assessments.get(key)
        if (
            not assessment
            or assessment.status != "VIOLATED"
            or not rule
            or rec.get("action") != rule.action
            or rec.get("execution_authorized") is not False
            or rec.get("verification_required") is not True
            or key in seen
        ):
            errors.append("Unsupported or unsafe recommendation")
        if target:
            for dep in target.depends_on:
                prior = assessments.get(dep.key)
                if (
                    prior is None
                    or prior.status == "UNRESOLVED"
                    or (prior.status == "VIOLATED" and dep.key not in seen)
                ):
                    errors.append("Unsafe remediation dependency order")
        seen.add(key)
    statuses = [a.status for a in report.assessments]
    expected = (
        "NON_COMPLIANT"
        if "VIOLATED" in statuses
        else "VERIFIED_WITHIN_SCOPE"
        if statuses
        and all(s == "SATISFIED" for s in statuses)
        and bundle.scope_complete
        and subject is not None
        else "INCONCLUSIVE"
    )
    if report.conclusion != expected:
        errors.append("Conclusion unsupported by obligations and scope")
    return errors
