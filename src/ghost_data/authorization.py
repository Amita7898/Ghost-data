"""Conservative request-intent grammar, not permission to execute destructive work.

Only supported first-person deletion requests are authorized for an audit. Negation,
conditional intent, quoted instructions and unresolved scope remain non-authorizing.
"""

import re
import unicodedata
from typing import Literal

Authorization = Literal["AUTHORIZED", "DECLINED", "NON_DELETION", "AMBIGUOUS"]
DELETE = r"\b(?:delet\w*|eras\w*|remov\w*|suppr(?:im|ess)\w*|effac\w*|elimin\w*|borr\w*|apag\w*|exclu\w*|exclus\w*|löschen|loeschen|gelöscht)\b"
OBJECT = r"(?:account|profile|(?:personal\s+)?(?:data|information)|records)"
EN_PREFIX = (
    r"^(?:then\s+)?(?:please\s+)?(?:(?:do\s+)?|(?:can|could|would|will)\s+you\s+(?:please\s+)?|"
    r"(?:i\s+(?:would\s+like|want|request)|i'd\s+like)\s+(?:you\s+)?to\s+)"
)
EN_END = r"(?=$|[.!?;,]|\s+(?:and|from|permanently|now|today|please|immediately|completely|entirely)\b)"
EN_ACTIVE = rf"{EN_PREFIX}(?:delete|erase|remove)\s+(?:all\s+(?:of\s+)?)?my\s+{OBJECT}\b{EN_END}"
EN_PASSIVE = rf"^(?:i\s+(?:want|request|would\s+like)|i'd\s+like)\s+(?:all\s+(?:of\s+)?)?my\s+{OBJECT}\s+(?:(?:to\s+be|permanently)\s+)*(?:deleted|erased|removed)\b{EN_END}"
POSITIVE = tuple(
    re.compile(p)
    for p in (
        EN_ACTIVE,
        EN_PASSIVE,
        rf"{EN_PREFIX}(?:delete|erase|remove)\s+(?:all\s+)?(?:the\s+)?(?:personal\s+)?(?:data|information)\s+you\s+(?:hold|have|store)\s+(?:about|on)\s+me\b{EN_END}",
        r"\b(?:supprimez|supprimer|effacez|effacer)\s+(?:toutes?\s+)?(?:mon\s+(?:compte|profil)|mes\s+données(?:\s+personnelles)?)\b",
        r"\bje\s+(?:demande|souhaite)\s+la\s+suppression\s+de\s+(?:mon\s+compte|mes\s+données)\b",
        r"\b(?:borra|borre|borren|elimina|elimine|eliminen)\s+(?:todos?\s+)?(?:mi\s+(?:cuenta|perfil)|mis\s+datos(?:\s+personales)?)\b",
        r"\b(?:apague|exclua|elimine|remova)\s+(?:todos?\s+(?:os\s+)?)?(?:minha\s+conta|meus\s+dados(?:\s+pessoais)?)\b",
        r"\b(?:solicito|peço|peco)\s+(?:a\s+)?exclus(?:ão|ao)\s+(?:permanente\s+)?(?:da\s+(?:minha\s+)?conta|dos\s+meus\s+dados)\b",
        r"\b(?:löschen|loeschen)\s+(?:sie\s+)?(?:bitte\s+)?(?:alle\s+)?(?:mein\s+(?:konto|profil)|meine\s+(?:persönlichen\s+)?daten)\b",
        r"^bitte\s+(?:mein\s+konto|meine\s+(?:persönlichen\s+)?daten)\s+(?:löschen|loeschen)\b",
    )
)


def classify(text: str) -> Authorization:
    """Classify supported intent; uncertain language never creates authorization."""
    t = (
        unicodedata.normalize("NFKC", text)
        .casefold()
        .translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    )
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) > 1 and t[0] in ("'", '"') and t[-1] == t[0]:
        return "AMBIGUOUS"
    deletion = bool(re.search(DELETE, t))
    if not deletion:
        return (
            "NON_DELETION"
            if re.search(
                r"\b(?:unsubscribe|marketing|mailing list|export|correct|subscription|promotional|access(?: to)? my|download my)\b",
                t,
            )
            else "AMBIGUOUS"
        )
    # Quoted commands are evidence about wording, not independent consent.
    if any(
        re.search(DELETE, m.group())
        for m in re.finditer(r"\"[^\"]*\"|(?<!\w)'[^']*'", t)
    ):
        return "AMBIGUOUS"
    # Explicit legal-retention exceptions are policy instructions, not consent reversal.
    t = re.sub(r"(?:do not|don't) delete records required by law", "", t)
    if re.search(r"(?:do not|don't).{0,20}(?:cancel|withdraw)", t):
        return "AMBIGUOUS"
    if re.search(r"\b(not|no|pas|nicht|não|nao)\b.{0,12}\b\1\b|don't\s+not", t):
        return "AMBIGUOUS"
    if re.search(
        r"\bnot\s+(?:sure|certain|ready)\b|\bcannot\s+decide\b|\b(?:if|unless|si|se|"
        r"wenn|hypothetically|suppose|pretend|considering)\b|\b(?:said|told|wrote|says|reads|displays|quoted|"
        r"example|phrase|tutorial|guide|previously|yesterday)\b",
        t,
    ):
        return "AMBIGUOUS"
    # Negative consent can span sentences; an embedded imperative cannot reverse it.
    if re.search(
        r"\b(?:not|cannot|can't|do not|don't|will not|won't)\s+"
        r"(?:consent(?:ing)?|authoriz(?:e|ing|ation)|authoris(?:e|ing|ation)|grant)\b|"
        r"\bnot\s+(?:what|something)\s+i\s+(?:want|request)\b|"
        r"(?:^|[.!?;,])\s*(?:no(?:\s+thanks)?|i\s+refuse|i\s+decline)\s*(?:$|[.!?;,])",
        t,
    ):
        return "DECLINED"
    if re.search(
        r"\b(?:button|screen|dialog|label|labelled|wording|means|definition)\b", t
    ):
        return "AMBIGUOUS"
    if re.search(
        r"(?:refuse to|decline to|refusing to|reject the request to|no longer want to|"
        r"do not|don't|never|haven't|have not|didn't|did not|won't|will not|wouldn't|"
        r"would not|not\s+(?:asking|requesting|want|authorized)|"
        r"not a request)[^.!?;]{0,55}(?:delet|eras|remov)|\b(?:withdraw|"
        r"cancel).{0,25}(?:deletion|erasure)|(?:\bne\b|\bn').{0,35}\b(?:pas|jamais)\b|"
        r"\bno\s+(?:elimin\w*|borr\w*)|\b(?:não|nao|nunca)\b.{0,40}(?:apag|exclu|"
        r"elimin|remov)|\b(?:nicht|niemals|kein|keine)\b",
        t,
    ):
        return "DECLINED"
    if re.search(
        r"\b(?:except|only|but keep|other than|on behalf of|someone else's)\b", t
    ):
        return "AMBIGUOUS"
    marketing_only = False
    for clause in re.split(r"(?<=[.!?;,])|\n", t):
        clause = clause.strip()
        if re.search(
            r"\b(?:from|off|out of)\b[^.!?;]{0,60}"
            r"\b(?:(?:marketing|mailing|newsletter|promotional)(?:\s+mailing)?\s+list|contact list)\b",
            clause,
        ):
            marketing_only = True
            continue
        if clause.endswith("?") and re.match(r"(?:delete|erase|remove)\b", clause):
            continue
        if re.search(
            r"\b(?:might|may|how|explain|why|when|whether|comment|pourquoi|cómo|como|wenn|wie)\b|^\s*(?:can|could|should|would|will)\s+i\b|^\s*(?:do|does|did|have|has|is|are)\s+(?:you|i|it|my|the)\b",
            clause,
        ):
            continue
        if any(pattern.search(clause.strip()) for pattern in POSITIVE):
            return "AUTHORIZED"
    if marketing_only or re.search(
        r"\b(?:delete|remove)\s+me\s+from\s+(?:your\s+)?(?:marketing|mailing|promotional)",
        t,
    ):
        return "NON_DELETION"
    return "AMBIGUOUS"
