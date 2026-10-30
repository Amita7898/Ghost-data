"""Offline aggregation of measured local-model results; never a runtime tool."""
import argparse
import hashlib
import json
import statistics
from pathlib import Path

def write_local_report(output,suite):
    output=Path(output);suite=Path(suite)
    result=json.loads((output/'results.json').read_text());summary={}
    for mode in sorted({row['mode'] for row in result['cases']}):
        rows=[row for row in result['cases'] if row['mode']==mode]
        accepted_valid=accepted_total=0
        for row in rows:
            raw=(suite/'visible'/f"{row['case']}.json").read_bytes();b=json.loads(raw);digest=hashlib.sha256(raw).hexdigest()
            for decision in row.get('decisions',[]):
                if not decision.get('accepted'):continue
                accepted_total+=1;p=decision['proposal']
                for index,o in enumerate(b['observations']):
                    uri=f'sha256:{digest}#/observations/{index}'
                    if p['evidence_id'] not in (o['id'],uri):continue
                    exact=f"Resource {o['resource']} in {o['system']} belongs to {row['report']['subject']}. Observed state: {p['value']}."
                    accepted_valid+=int(p['system']==o['system'] and p['resource']==o['resource'] and p.get('quote')==exact and exact in o.get('fields',{}).get('note','') and decision.get('source')==uri and o['kind']=='READBACK')
        supported=sum(row['expected']=='VERIFIED_WITHIN_SCOPE' for row in rows)
        summary[mode]={'cases':len(rows),'accuracy':sum(row['correct'] for row in rows)/len(rows),
            'completion_rate':sum(row['status']=='completed' for row in rows)/len(rows),
            'unsupported_verified':sum(row['unsupported_verified'] for row in rows),
            'incorrect_noncompliant':sum(row['predicted']=='NON_COMPLIANT' and row['expected']!='NON_COMPLIANT' for row in rows),
            'median_seconds':statistics.median(row['seconds'] for row in rows),'total_seconds':sum(row['seconds'] for row in rows),
            'model_calls':sum((row.get('usage') or {}).get('model_calls',0) for row in rows),
            'input_tokens':sum((row.get('usage') or {}).get('input_tokens',0) for row in rows),
            'output_tokens':sum((row.get('usage') or {}).get('output_tokens',0) for row in rows),
            'tool_calls':sum(row['tool_calls'] for row in rows),'tool_result_errors':sum(row['tool_argument_errors'] for row in rows),
            'accepted_proposals':sum(row['accepted'] for row in rows),'rejected_proposals':sum(row['rejected'] for row in rows),
            'verification_coverage':sum(row['predicted']=='VERIFIED_WITHIN_SCOPE' for row in rows if row['expected']=='VERIFIED_WITHIN_SCOPE')/supported if supported else None,
            'agent_discoveries':sum(row['agent_discovery'] for row in rows),'accepted_citations_valid':accepted_valid,'accepted_citations_total':accepted_total}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    lines=['# Measured local-model comparison','', '| Mode | Cases | Accuracy | Completed | Unsupported verified | Median seconds |','|---|---:|---:|---:|---:|---:|']
    for mode,s in summary.items():lines.append(f"| {mode} | {s['cases']} | {s['accuracy']:.0%} | {s['completion_rate']:.0%} | {s['unsupported_verified']} | {s['median_seconds']:.3f} |")
    lines+=['','These are small controlled receipt-contract diagnostics. See results.json for all timings, usage, proposals and failures. Source checks validate literal citation correspondence for this contract; they are not independent source-authenticity attestations. Zero accepted citations is undefined precision, not perfect precision. Missing usage after failed calls is unknown, not zero compute.','']
    (output/'metrics.md').write_text('\n'.join(lines))
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output');parser.add_argument('--suite',required=True)
    args=parser.parse_args();write_local_report(args.output,args.suite)
