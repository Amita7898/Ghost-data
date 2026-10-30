import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import statistics
import platform
import sys
import time
from .adapters import adapter_for,MODES
from .score import score
from .generate import encoded

def fraction(n,d):return n/d if d else None

def summarize(rows):
    scores=[r['scores'] for r in rows]
    total=lambda k:sum(s[k] for s in scores)
    times=[t for r in rows for t in r['seconds']]
    return dict(cases=len(rows),runtime_error_cases=sum(bool(r['errors']) for r in rows),conclusion_accuracy=fraction(total('correct'),len(rows)),
        unsupported_verified=total('unsupported_verified'),incorrect_noncompliant=total('incorrect_noncompliant'),
        authorization_accuracy=fraction(total('authorization_correct'),len(rows)),
        unsafe_refusals=sum(not s['refusal_safely_handled'] for s in scores),
        evidence_attribution=fraction(total('valid_citations'),total('citations')),
        valid_citations=total('valid_citations'),citations=total('citations'),
        verification_coverage=fraction(total('verification_covered'),total('verification_supported')),
        verification_covered=total('verification_covered'),verification_supported=total('verification_supported'),
        policy_violations=total('policy_violations'),timestamp_violations=total('timestamp_violations'),
        world_state_accuracy_when_decisive=fraction(total('world_correct'),total('world_decisive')),
        world_decisive=total('world_decisive'),world_state_decision_rate=fraction(total('world_decisive'),len(rows)),
        repeated_outputs_identical=all(r['deterministic'] for r in rows),
        median_ms=statistics.median(times)*1000,p95_ms=sorted(times)[max(0,int(len(times)*.95+.999)-1)]*1000,
        total_runtime_seconds=sum(times))

def evaluate(suite,adapter=None,repeats=2):
    if repeats<1:raise ValueError('repeats must be positive')
    adapter=adapter or adapter_for('deterministic');suite=Path(suite)
    manifest=json.loads((suite/'manifest.json').read_text());rows=[]
    # Timing excludes scoring; first call includes lazy imports (cold start).
    for item in manifest['cases']:
        sid=item['id']
        if len(sid)!=16 or any(c not in '0123456789abcdef' for c in sid):raise ValueError('Invalid scenario id')
        raw=(suite/'visible'/f'{sid}.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('Suite input hash mismatch')
        reports=[];times=[];errors=[]
        for _ in range(repeats):
            start=time.perf_counter()
            try:
                reports.append(adapter.predict(raw))
            except Exception as exc:
                # Exception classes only: provider errors may contain secrets.
                errors.append(type(exc).__name__)
                reports.append(dict(conclusion='ERROR',authorization='ERROR',assessments=[],recommendations=[]))
            times.append(time.perf_counter()-start)
        # Labels loaded only AFTER runtime inference; never passed to adapter.
        hidden=json.loads((suite/'evaluator_only'/f'{sid}.json').read_text())
        if hidden['input_sha256']!=item['sha256']:raise ValueError('Expected/input pairing mismatch')
        expected=hidden['expected'];visible=json.loads(raw)
        rows.append(dict(id=sid,family=hidden['world']['family'],expected=expected['conclusion'],
            predicted=reports[0]['conclusion'],world_state=expected['world_state'],scores=score(reports[0],expected,visible),
            seconds=times,errors=errors,deterministic=not errors and all(r==reports[0] for r in reports),report=reports[0]))
    if not rows:raise ValueError('Empty suite')
    grouped=defaultdict(list);categories=defaultdict(list)
    for row in rows:grouped[row['family']].append(row);categories[row['expected']].append(row)
    return dict(mode=adapter.name,seed=manifest['seed'],repeats=repeats,environment=dict(python=sys.version,platform=platform.platform()),suite_manifest_sha256=hashlib.sha256(encoded(manifest)).hexdigest(),summary=summarize(rows),
        by_family={k:summarize(v) for k,v in sorted(grouped.items())},
        by_conclusion={k:summarize(v) for k,v in sorted(categories.items())},cases=rows,
        usage=dict(model_calls=0,input_tokens=0,output_tokens=0,api_cost_usd=0) if adapter.name=='deterministic' else None)

def markdown(result):
    s=result['summary'];lines=['# Synthetic benchmark results','',f"Mode: {result['mode']}; seed: {result['seed']}; repeated runs: {result['repeats']}.",'',
        'Metrics describe generated scenarios, not real-world accuracy or LLM performance.','', '| Metric | Value |','|---|---|']
    lines += [f'| {k} | {v} |' for k,v in s.items()]
    for title,key in [('By expected conclusion','by_conclusion'),('By scenario family','by_family')]:
        lines += ['',f'## {title}','','| Category | Cases | Conclusion accuracy | Unsupported verified |','|---|---:|---:|---:|']
        lines += [f"| {k} | {v['cases']} | {v['conclusion_accuracy']:.3f} | {v['unsupported_verified']} |" for k,v in result[key].items()]
    lines += ['','## Failures','','| Scenario | Family | Expected | Actual |','|---|---|---|---|']
    lines += [f"| {r['id']} | {r['family']} | {r['expected']} | {r['predicted']} |" for r in result['cases'] if not r['scores']['correct'] or r['scores']['policy_violations']]
    lines += ['','Evidence attribution counts cited IDs that are valid for the same subject/resource and eligible timestamps. Verification coverage counts correctly satisfied, provable obligations, not all real-world resources. World-state accuracy is selective: inconclusive and not-applicable outputs abstain. Timing is local wall-clock inference time; JSON reports retain each measurement. No runtime model calls were made in deterministic mode.','']
    return '\n'.join(lines)

def main():
    p=argparse.ArgumentParser(description='Benchmark without exposing labels to the runtime adapter')
    p.add_argument('suite',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--mode',choices=MODES,default='deterministic');p.add_argument('--repeats',type=int,default=2)
    a=p.parse_args();result=evaluate(a.suite,adapter_for(a.mode),a.repeats)
    if a.output.exists():raise ValueError('Report destination exists; refusing to overwrite')
    a.output.mkdir(parents=True)
    (a.output/'results.json').write_bytes(encoded(result));(a.output/'report.md').write_text(markdown(result))
    print(json.dumps(result['summary'],indent=2))

if __name__=='__main__':main()
