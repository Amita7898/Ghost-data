"""Recommendations only. Cycles or missing dependencies block the action plan."""
def plan(bundle, assessments):
    violated = {(a.system,a.resource) for a in assessments if a.status == 'VIOLATED'}
    rules = {r.category:r for r in bundle.rules}
    targets = {t.key:t for t in bundle.targets}
    pending = {k for k in violated if targets[k].category in rules}
    statuses = {(a.system,a.resource):a.status for a in assessments}
    for k in pending:
        if any(statuses.get(d.key) not in ('SATISFIED', 'VIOLATED') for d in targets[k].depends_on):
            return (), ('Dependency state unresolved; plan withheld',)
    ordered = []
    while pending:
        ready = sorted(k for k in pending if all(d.key not in pending and d.key in targets
                                               for d in targets[k].depends_on))
        if not ready:
            return (), ('Remediation dependencies unresolved or cyclic; plan withheld',)
        # Prefer disabling recreation paths, while preserving explicit dependencies.
        ready.sort(key=lambda k:(rules[targets[k].category].action not in ('DISABLE','BLOCK'), k))
        k = ready[0]
        pending.remove(k)
        ordered.append({'system':k[0], 'resource':k[1], 'action':rules[targets[k].category].action,
                        'verification_required':True, 'execution_authorized':False})
    return tuple(ordered), ()
