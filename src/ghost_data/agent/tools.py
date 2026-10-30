"""Typed bounded tools. Objects come only from the registered visible bundle."""
import json
import re
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from ..models import Resource,Identifier,Bundle
from ..identity import subject_for_request,resolve,normalized
from ..evidence import eligible,provenance
from ..engine import audit

class Args(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class ContextArgs(Args): pass
class SearchArgs(Args):
    query:str=Field(default='',max_length=120)
    offset:int=Field(default=0,ge=0,le=10000)
class ReadArgs(Args):
    evidence_id:str=Field(min_length=1,max_length=120)
class IdentityArgs(Args):
    kind:Literal['email','user_id','phone','hash']
    value:str=Field(min_length=1,max_length=200)
class HistoryArgs(Args):
    system:str=Field(min_length=1,max_length=120)
    resource:str=Field(min_length=1,max_length=120)
class ProposalArgs(HistoryArgs):
    evidence_id:str=Field(min_length=1,max_length=120)
    claim:Literal['STATE','IDENTITY','RELATIONSHIP']
    value:str=Field(min_length=1,max_length=200)
    quote:str=Field(default='',max_length=1000,description='For a resource_readback_note, copy the exact Resource ... Observed state: ... sentence from note. Otherwise use empty string.')

DEFINITIONS={
 'get_context':(ContextArgs,'Get trusted scope, unresolved obligations and resource identifiers; no evidence text.'),
 'search_evidence':(SearchArgs,'Search eligible subject-linked observations matching ANY query token. Query may be empty. Paginate 8 at a time.'),
 'read_evidence':(ReadArgs,'Read one registered eligible observation and its exact source locator.'),
 'resolve_identity':(IdentityArgs,'Resolve a typed identifier through registered current and historical identity rows.'),
 'inspect_resource':(HistoryArgs,'Inspect eligible history, readback/claim type and snapshot coverage for one scoped resource.'),
 'submit_hypothesis':(ProposalArgs,'Validate a STATE value or IDENTITY subject against cited source. RELATIONSHIP uses an explicit system/resource dependency key. For prose READBACK notes, supply the exact source sentence in quote; the source contract must support it. Rejected hypotheses must not be reported as facts.')}

def schemas():
    return [{'type':'function','function':{'name':name,'description':desc,'parameters':cls.model_json_schema()}} for name,(cls,desc) in DEFINITIONS.items()]

class Tools:
    def __init__(self,bundle: Bundle,digest: str):
        self.bundle=bundle;self.digest=digest;self.subject=subject_for_request(bundle)
        self.report=audit(bundle,digest);self.sources=provenance(bundle,digest)
        self.accepted=[];self.rejected=[];self.calls=0
    def observations(self):
        if not self.subject or self.report.authorization!='AUTHORIZED':return []
        return [o for t in self.bundle.targets for o in eligible(self.bundle,t,self.subject)]
    def execute(self,name: str,args: dict) -> dict:
        self.calls+=1
        if name not in DEFINITIONS:return {'error':'Unknown tool'}
        try:
            arg=DEFINITIONS[name][0].model_validate(args)
        except ValueError:return {'error':'Invalid typed tool arguments'}
        b=self.bundle;obs=self.observations()
        if name=='get_context':
            result={'request':b.request.model_dump(mode='json'),'subject':self.subject,
                    'authorization':self.report.authorization,'policies':[r.model_dump(mode='json') for r in b.rules[:20]],'targets':[t.model_dump(mode='json') for t in b.targets[:20]],
                    'targets_truncated':len(b.targets)>20,'unresolved':list(self.report.unresolved)[:20],
                    'instruction':'Inspect evidence with tools; conclusions are issued by the deterministic kernel.'}
        elif name=='search_evidence':
            terms=re.findall(r'[\w@.+:-]+',arg.query.casefold())
            matches=[o for o in obs if not terms or any(term in json.dumps(o.model_dump(mode='json')).casefold() for term in terms)]
            result={'total':len(matches),'offset':arg.offset,'items':[{'id':o.id,'system':o.system,'resource':o.resource,'kind':o.kind,'source':self.sources[o.id]} for o in matches[arg.offset:arg.offset+8]]}
        elif name=='read_evidence':
            o=next((o for o in obs if o.id==arg.evidence_id or self.sources[o.id]==arg.evidence_id),None)
            result={'evidence_id':o.id,'observation':o.model_dump(mode='json'),'source':self.sources[o.id]} if o else {'error':'Evidence not in eligible subject scope'}
        elif name=='resolve_identity':
            ident=Identifier(kind=arg.kind,value=arg.value)
            if not self.subject or not any(normalized(i.identifier)==normalized(ident) and i.subject==self.subject and i.recorded_at<=b.request.audit_at for i in b.identities):
                result={'error':'Identifier outside subject scope'}
            else:
                matched=[(n,i) for n,i in enumerate(b.identities) if normalized(i.identifier)==normalized(ident) and i.recorded_at<=b.request.audit_at]
                ambiguous=len({i.subject for _,i in matched})!=1
                rows=matched if ambiguous else [(n,i) for n,i in enumerate(b.identities) if i.subject==self.subject and i.recorded_at<=b.request.audit_at]
                result={'history_truncated':len(rows)>10,'rows':[{'identity':i.model_dump(mode='json'),'source':self.sources[f'identities:{n}']} for n,i in rows[:10]],
                        'ambiguous':ambiguous}
        elif name=='inspect_resource':
            target=next((t for t in b.targets if t.key==(arg.system,arg.resource)),None)
            rows=[o for o in obs if o.key==(arg.system,arg.resource)]
            result={'target':target.model_dump(mode='json'),'history':[{'id':o.id,'state':o.state,'kind':o.kind,'coverage':o.coverage,'observed_at':o.observed_at.isoformat(),'source':self.sources[o.id]} for o in rows[:10]]} if target else {'error':'Resource outside scope'}
        else:
            o=next((o for o in obs if (o.id==arg.evidence_id or self.sources[o.id]==arg.evidence_id) and o.key==(arg.system,arg.resource)),None)
            before_bundle=self.bundle;before_report=self.report
            supported=False;reason='Citation does not support claim'
            if o and arg.claim=='STATE' and arg.quote:
                from .interpretation import interpret
                derived=interpret(o,self.subject,arg.quote,arg.value)
                if derived:
                    self.bundle=self.bundle.model_copy(update={'observations':tuple(derived if x.id==o.id else x for x in self.bundle.observations)})
                    self.report=audit(self.bundle,self.digest)
                    o=derived
            if o:
                if arg.claim=='STATE':
                    target_assessment=next((a for a in self.report.assessments if (a.system,a.resource)==o.key),None)
                    supported=(o.kind=='READBACK' and o.observed_at==b.request.audit_at and o.state==arg.value
                               and (o.state!='ABSENT' or o.coverage=='EXACT_RESOURCE')
                               and target_assessment is not None and target_assessment.status!='UNRESOLVED')
                elif arg.claim=='IDENTITY':
                    supported=arg.value==self.subject and resolve(o.identifier,o.observed_at,b.request.audit_at,b.identities)=={self.subject}
                else:
                    # No guessed edges: a row must explicitly name the relationship.
                    target=next((t for t in b.targets if t.key==o.key),None)
                    supported=bool(target and any(f'{d.system}/{d.resource}'==arg.value for d in target.depends_on)
                                   and o.fields.get('depends_on')==arg.value)
            if not supported:
                self.bundle=before_bundle;self.report=before_report
            result={'accepted':bool(supported),'proposal':arg.model_dump(),'reason':'Supported by registered source and proof rules' if supported else reason,
                    'source':self.sources[o.id] if o else None}
            if len(json.dumps(result))<=6000:
                (self.accepted if supported else self.rejected).append(result)
        # Do not silently crop JSON or remove qualifiers.
        if len(json.dumps(result))>6000:return {'error':'Result too large; narrow the query or source fragment'}
        return result
