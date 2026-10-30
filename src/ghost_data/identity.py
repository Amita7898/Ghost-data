"""Time-aware typed identity matching. Shared aliases remain ambiguous."""
def normalized(identifier):
    value = identifier.value.strip()
    if identifier.kind in ('email', 'hash'):
        value = value.casefold()
    return identifier.kind, value

def resolve(identifier, at, cutoff, identities):
    return {i.subject for i in identities
            if normalized(i.identifier) == normalized(identifier)
            and i.recorded_at <= cutoff and i.valid_from <= at
            and (i.valid_to is None or at < i.valid_to)}

def subject_for_request(bundle):
    r = bundle.request
    # An old email may be deliberately supplied; preserve ambiguity if reassigned.
    candidates = {i.subject for i in bundle.identities
                  if normalized(i.identifier) == normalized(r.identifier)
                  and i.recorded_at <= r.audit_at and i.valid_from <= r.requested_at}
    return next(iter(candidates)) if len(candidates) == 1 else None
