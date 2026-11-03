"""Pure audit orchestration, shared by CLI and future API/agent."""

from .authorization import classify
from .evidence import provenance
from .identity import subject_for_request
from .models import Assessment, Bundle, Report
from .planning import plan
from .policy import assess
from .verifier import check


def audit(bundle: Bundle, digest: str) -> Report:
    """Assess registered scope, then independently check the proposed report."""
    auth = classify(bundle.request.text)
    subject = subject_for_request(bundle)
    assessments = ()
    unresolved = []
    recommendations = ()
    if auth != "AUTHORIZED":
        conclusion = (
            "NOT_APPLICABLE" if auth in ("DECLINED", "NON_DELETION") else "INCONCLUSIVE"
        )
        if auth == "AMBIGUOUS":
            unresolved.append("Request wording requires review; no deletion authorized")
    else:
        if subject is None:
            assessments = tuple(
                Assessment(
                    system=t.system,
                    resource=t.resource,
                    status="UNRESOLVED",
                    reason="Identity unresolved or ambiguous",
                )
                for t in bundle.targets
            )
            unresolved.append("Identity unresolved or ambiguous")
        else:
            assessments = tuple(
                assess(bundle, t, subject)
                for t in sorted(bundle.targets, key=lambda t: t.key)
            )
        if not bundle.scope_complete:
            unresolved.append(
                "Discovery coverage is not declared complete within the supplied scope"
            )
        if not assessments:
            unresolved.append("No resource inventory supplied")
        statuses = [a.status for a in assessments]
        conclusion = (
            "NON_COMPLIANT"
            if "VIOLATED" in statuses
            else "VERIFIED_WITHIN_SCOPE"
            if statuses and all(s == "SATISFIED" for s in statuses) and not unresolved
            else "INCONCLUSIVE"
        )
        recommendations, planning_gaps = plan(bundle, assessments)
        unresolved.extend(planning_gaps)
        unresolved.extend(
            f"{a.system}/{a.resource}: {a.reason}"
            for a in assessments
            if a.status == "UNRESOLVED"
        )
    report = Report(
        conclusion=conclusion,
        authorization=auth,
        subject=subject,
        artifact_sha256=digest,
        assessments=assessments,
        recommendations=recommendations,
        unresolved=tuple(unresolved),
        provenance=provenance(bundle, digest),
    )
    errors = check(bundle, report)
    if errors:
        report = report.model_copy(
            update={
                "conclusion": "INCONCLUSIVE",
                "recommendations": (),
                "validation_errors": tuple(errors),
            }
        )
    return report
