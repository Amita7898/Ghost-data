"""Conservative supported-language grammar; unfamiliar wording requires review."""
import re

def classify(text):
    t = text.casefold().replace('’', "'").strip()
    # Bound supported multilingual refusal forms; unfamiliar syntax stays ambiguous.
    if re.search(r"\b(?:nicht|pas|no)\b.{0,20}\b(?:nicht|pas|no)\b", t):
        return 'AMBIGUOUS'
    if (re.search(r"\b(?:löschen|loeschen|gelöscht)\b", t)
            and re.search(r"\b(?:nicht|niemals|kein|keine)\b", t)):
        return 'DECLINED'
    # Do not collapse double negation into refusal or consent.
    if re.search(r"(?:do not|don't).{0,20}(?:cancel|withdraw)", t):
        return 'AMBIGUOUS'
    if re.search(r"(?:do not|don't|never).{0,30}(?:delete|erase|remove|deletion|erasure)|not (?:asking|requesting).{0,30}(?:deletion|erase)|not a request.{0,20}(?:erase|deletion)|(?:withdraw|cancel).{0,20}(?:deletion|erasure)|ne\s+supprimez\s+pas|no\s+(?:elimines|borres)", t):
        # Scope exceptions are understood only for the explicit law-retention form.
        t_without_exception = re.sub(r'(?:do not|don\x27t) delete records required by law', '', t)
        if t_without_exception == t or classify(t_without_exception) != 'AUTHORIZED':
            return 'DECLINED'
        return 'AUTHORIZED'
    clauses = re.split(r'[.!?;\n]+', t)
    for clause in clauses:
        if re.search(r'\b(?:if|might|may|considering|explain|how|suppose|hypothetically)\b', clause):
            continue
        if re.search(r'\b(?:delete|erase|remove) my (?:account|profile|personal data|personal information)\b', clause):
            return 'AUTHORIZED'
        if 'je demande la suppression de mon compte' in clause or 'solicito a exclusão permanente da conta' in clause:
            return 'AUTHORIZED'
    if re.search(r'\b(?:unsubscribe|marketing|mailing list|export|correct|subscription|promotional)\b', t) and not re.search(r'delet|eras|supprim|elimin', t):
        return 'NON_DELETION'
    return 'AMBIGUOUS'
