"""Offline reference adjudicator, independent of all ghost_data kernel modules.

This evaluates the generator's documented evidence contract, not kernel output.
Labels are never embedded in the visible projection.
"""

from datetime import datetime


def time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def expected(world, visible, quality):
    cutoff = time(world["cutoff"])
    subject = world["subject"]

    def norm(i):
        return i["kind"], i["value"].strip().casefold() if i["kind"] in (
            "email",
            "hash",
        ) else i["value"].strip()

    aliases = {
        i["subject"]
        for i in visible["identities"]
        if norm(i["identifier"]) == norm(visible["request"]["identifier"])
        and time(i["recorded_at"]) <= cutoff
    }
    ownership_known = aliases == {subject}
    obligations = []
    for r in world["resources"]:
        target = next(
            t
            for t in visible["targets"]
            if t["system"] == r["system"] and t["resource"] == r["resource"]
        )
        rows = []
        allowed = []
        outcomes = []
        condition_known = (
            not r.get("condition") or target["conditions"].get(r["condition"]) is True
        )
        for o in visible["observations"]:
            if (o["system"], o["resource"]) != (r["system"], r["resource"]):
                continue
            at = time(o["observed_at"])
            owners = {
                i["subject"]
                for i in visible["identities"]
                if norm(i["identifier"]) == norm(o["identifier"])
                and time(i["recorded_at"]) <= cutoff
                and time(i["valid_from"]) <= at
                and (not i.get("valid_to") or at < time(i["valid_to"]))
            }
            temporal = (
                at == cutoff
                and time(o["captured_at"]) <= cutoff
                and time(o["fields"].get("ingested_at", o["captured_at"])) <= cutoff
            )
            if (
                not ownership_known
                or owners != {subject}
                or not quality[o["id"]]["attribution_valid"]
                or not temporal
                or o["kind"] != "READBACK"
            ):
                continue
            allowed.append(o["id"])
            if not condition_known:
                continue
            outcome = None
            if r["action"] in ("DELETE", "RETAIN"):
                if o["state"] == "PRESENT":
                    outcome = r["action"] == "RETAIN"
                if o["state"] == "ABSENT" and o["coverage"] == "EXACT_RESOURCE":
                    outcome = r["action"] == "DELETE"
            elif r["action"] == "BLOCK":
                if o.get("archive_present") is True and o["state"] in (
                    "ACTIVE",
                    "BLOCKED",
                ):
                    outcome = o["state"] == "BLOCKED"
            elif r["action"] in ("REDACT", "ANONYMIZE"):
                fields = o["fields"]
                if o["state"] == "PRESENT":
                    if any(
                        fields.get(f) not in (None, "") for f in r["required_fields"]
                    ):
                        outcome = False
                    elif all(f in fields for f in r["required_fields"]) and (
                        not r["preserve"] or fields.get("subject_reference") == subject
                    ):
                        if r["action"] == "REDACT" or o.get("unlinking_verified"):
                            outcome = True
            rows.append(o["id"])
            outcomes.append(outcome)
        status = "UNRESOLVED"
        if outcomes and all(x is True for x in outcomes):
            status = "SATISFIED"
        elif outcomes and all(x is False for x in outcomes):
            status = "VIOLATED"
        obligations.append(
            dict(
                system=r["system"],
                resource=r["resource"],
                status=status,
                allowed_evidence=allowed,
            )
        )
    statuses = [o["status"] for o in obligations]
    if world["intent"] in ("DECLINED", "NON_DELETION"):
        conclusion = "NOT_APPLICABLE"
    elif world["intent"] == "AMBIGUOUS":
        conclusion = "INCONCLUSIVE"
    elif "VIOLATED" in statuses:
        conclusion = "NON_COMPLIANT"
    elif all(s == "SATISFIED" for s in statuses):
        conclusion = "VERIFIED_WITHIN_SCOPE"
    else:
        conclusion = "INCONCLUSIVE"
    if world["intent"] != "AUTHORIZED":
        obligations = []
    actual = []
    for r in world["resources"]:
        if r.get("condition") and not r["conditions"].get(r["condition"]):
            continue
        desired = {
            "DELETE": "ABSENT",
            "RETAIN": "PRESENT",
            "REDACT": "PRESENT",
            "ANONYMIZE": "PRESENT",
            "BLOCK": "BLOCKED",
        }[r["action"]]
        compliant = r["actual"] == desired
        if r["action"] in ("REDACT", "ANONYMIZE"):
            compliant = compliant and all(
                f in r["actual_fields"] and r["actual_fields"][f] in (None, "")
                for f in r["required_fields"]
            )
            if r["preserve"]:
                compliant = (
                    compliant and r["actual_fields"].get("subject_reference") == subject
                )
            if r["action"] == "ANONYMIZE":
                compliant = compliant and r["actual_unlinked"]
        if r["action"] == "BLOCK":
            compliant = compliant and r["archive_present"]
        actual.append(compliant)
    return dict(
        conclusion=conclusion,
        authorization=world["intent"],
        world_state="COMPLIANT" if all(actual) else "NON_COMPLIANT",
        obligations=obligations,
    )
