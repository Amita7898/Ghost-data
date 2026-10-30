"""Constrained source-backed interpretation, never free-form assertion authority.

An adapter marks an already registered READBACK as a prose state receipt. The
LLM locates its exact receipt sentence. An independent grammar then validates
subject, system, resource and observed state. This intentionally narrow bridge
is extensible only by adding reviewed source contracts and tests.
"""
import re

def interpret(observation,subject,quote,state):
    if observation.kind!='READBACK' or observation.state!='UNKNOWN':return None
    if observation.fields.get('source_kind')!='resource_readback_note':return None
    text=observation.fields.get('note')
    if not isinstance(text,str) or not quote or quote not in text:return None
    pattern=r'Resource (\S+) in (\S+) belongs to (\S+)\. Observed state: (ABSENT|PRESENT)\.'
    match=re.fullmatch(pattern,quote)
    if not match or match.groups()!=(observation.resource,observation.system,subject,state):return None
    # Contradictory source sentences cannot be selectively quoted.
    mentions=[m for m in re.finditer(pattern,text) if m.group(1)==observation.resource and m.group(2)==observation.system]
    if any(m.group(3)!=subject or m.group(4)!=state for m in mentions):return None
    if state=='ABSENT' and observation.coverage!='EXACT_RESOURCE':return None
    return observation.model_copy(update={'state':state})
