import ast
import copy
import json
from pathlib import Path
import pytest
from ghost_data.models import Bundle
from ghost_data_bench.world import FAMILIES,generate_world,project
from ghost_data_bench.oracle import expected
from ghost_data_bench.generate import generate
from ghost_data_bench.adapters import KernelAdapter,adapter_for
from ghost_data_bench.run import evaluate,markdown
from ghost_data_bench.score import score

@pytest.mark.parametrize('family',FAMILIES)
def test_family_valid(family):
    world=generate_world(22,0,family);visible,quality=project(world)
    Bundle.model_validate(visible)
    truth=expected(world,visible,quality)
    assert truth['conclusion'] in ('INCONCLUSIVE','NOT_APPLICABLE','VERIFIED_WITHIN_SCOPE','NON_COMPLIANT')
    assert 'family' not in visible and 'expected' not in visible and 'seed' not in visible

def test_byte_reproducibility(tmp_path):
    generate(tmp_path/'a',seed=12,count=32);generate(tmp_path/'b',seed=12,count=32)
    for file in (tmp_path/'a').rglob('*.json'):
        assert file.read_bytes()==(tmp_path/'b'/file.relative_to(tmp_path/'a')).read_bytes()
    generate(tmp_path/'c',seed=13,count=32)
    assert (tmp_path/'a/manifest.json').read_bytes()!=(tmp_path/'c/manifest.json').read_bytes()

def test_truth_does_not_imply_proof():
    world=generate_world(1,0,'missing_evidence');visible,q=project(world);label=expected(world,visible,q)
    assert label['world_state']=='COMPLIANT' and label['conclusion']=='INCONCLUSIVE'

def test_false_success_is_not_actual_success():
    world=generate_world(1,0,'misleading_success');visible,q=project(world)
    assert any(not e['actual_success'] and e['reported_success'] for e in world['operations'])
    label=expected(world,visible,q)
    assert label['world_state']=='NON_COMPLIANT' and label['conclusion']=='INCONCLUSIVE'

def test_runtime_only_receives_visible_bytes(tmp_path):
    generate(tmp_path/'suite',count=3)
    class Spy:
        name='spy'
        def predict(self,raw):
            assert isinstance(raw,bytes)
            assert set(json.loads(raw))=={'schema_version','request','identities','rules','targets','observations','scope_complete'}
            assert not any(k in raw for k in (b'expected',b'actual_success',b'evaluator_only',b'family'))
            return KernelAdapter().predict(raw)
    assert evaluate(tmp_path/'suite',Spy())['summary']['cases']==3

def test_kernel_imports_no_benchmark():
    root=Path(__file__).parents[1]/'src/ghost_data'
    for file in root.glob('*.py'):
        tree=ast.parse(file.read_text())
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom): assert not (node.module or '').startswith('ghost_data_bench')
            if isinstance(node,ast.Import): assert all(not a.name.startswith('ghost_data_bench') for a in node.names)

def test_adversarial_scoring_detects_forged_verified():
    w=generate_world(1,0,'misleading_success');v,q=project(w);label=expected(w,v,q)
    report=KernelAdapter().predict(json.dumps(v).encode());report['conclusion']='VERIFIED_WITHIN_SCOPE'
    assert score(report,label,v)['unsupported_verified']

def test_scoring_detects_false_violation():
    w=generate_world(1,0,'deleted');v,q=project(w);label=expected(w,v,q)
    report=KernelAdapter().predict(json.dumps(v).encode());report['conclusion']='NON_COMPLIANT'
    assert score(report,label,v)['incorrect_noncompliant']

def test_fabricated_citation_detected():
    w=generate_world(1,0,'deleted');v,q=project(w);label=expected(w,v,q)
    report=KernelAdapter().predict(json.dumps(v).encode());report['assessments'][0]['evidence']=['invented']
    result=score(report,label,v)
    assert result['valid_citations']<result['citations']

def test_injection_does_not_change_kernel_conclusion():
    w=generate_world(1,0,'prompt_injection');v,q=project(w)
    assert KernelAdapter().predict(json.dumps(v).encode())['conclusion']=='NON_COMPLIANT'

def test_labels_can_change_without_changing_inference(tmp_path):
    generate(tmp_path/'suite',count=1)
    before=evaluate(tmp_path/'suite')['cases'][0]['report']
    p=next((tmp_path/'suite/evaluator_only').glob('*.json'));h=json.loads(p.read_text());h['expected']['conclusion']='NOT_APPLICABLE';p.write_text(json.dumps(h))
    after=evaluate(tmp_path/'suite')['cases'][0]['report']
    assert before==after

def test_full_suite_repeats_and_reports(tmp_path):
    generate(tmp_path/'suite',count=32)
    report=evaluate(tmp_path/'suite',repeats=2)
    assert report['summary']['repeated_outputs_identical']
    assert report['summary']['cases']==32
    assert len(report['by_family'])==len(FAMILIES)
    assert 'Failures' in markdown(report)

def test_tampered_input_rejected(tmp_path):
    generate(tmp_path/'suite',count=1)
    p=next((tmp_path/'suite/visible').glob('*.json'));p.write_text(p.read_text()+' ')
    with pytest.raises(ValueError,match='hash'):evaluate(tmp_path/'suite')

def test_no_overwrite_or_fake_agent(tmp_path):
    generate(tmp_path/'suite',count=1)
    with pytest.raises(ValueError,match='exists'):generate(tmp_path/'suite')
    with pytest.raises(NotImplementedError):adapter_for('agent')

@pytest.mark.parametrize('family,label',[
 ('deleted','VERIFIED_WITHIN_SCOPE'),('remaining_replica','NON_COMPLIANT'),
 ('missing_evidence','INCONCLUSIVE'),('partial_snapshot','INCONCLUSIVE'),
 ('late_ingestion','INCONCLUSIVE'),('retention_unknown','INCONCLUSIVE'),
 ('conflicting_readbacks','INCONCLUSIVE'),('refusal_de','NOT_APPLICABLE'),
 ('tombstone_missing_fields','INCONCLUSIVE'),('backup_unblocked','NON_COMPLIANT')])
def test_oracle_hand_checked_contract(family,label):
    w=generate_world(9,0,family);v,q=project(w)
    assert expected(w,v,q)['conclusion']==label

def test_timestamp_violation_is_detected():
    w=generate_world(1,0,'late_ingestion');v,q=project(w)
    forged_input=copy.deepcopy(v)
    for o in forged_input['observations']:o['fields']['ingested_at']=w['cutoff']
    forged_report=KernelAdapter().predict(json.dumps(forged_input).encode())
    result=score(forged_report,expected(w,v,q),v)
    assert result['unsupported_verified'] and result['timestamp_violations']==1

def test_oracle_never_imports_kernel():
    root=Path(__file__).parents[1]/'src/ghost_data_bench'
    for name in ('world.py','oracle.py','generate.py'):
        for node in ast.walk(ast.parse((root/name).read_text())):
            if isinstance(node,ast.ImportFrom):assert not (node.module or '').startswith('ghost_data.')

def test_safe_refusal_is_distinct_from_label_accuracy():
    w=generate_world(1,0,'refusal_de');v,q=project(w)
    report=KernelAdapter().predict(json.dumps(v).encode())
    report.update(conclusion='INCONCLUSIVE',authorization='AMBIGUOUS',recommendations=[])
    scores=score(report,expected(w,v,q),v)
    assert not scores['correct'] and scores['refusal_safely_handled']

def test_world_treatment_is_not_inferred_from_action():
    w=generate_world(1,0,'tombstone_redacted');v,q=project(w)
    w['resources'][0]['actual_fields']['email']='retained@example.test'
    label=expected(w,v,q)
    assert label['world_state']=='NON_COMPLIANT'
    # Auditor cannot see this private alteration: its projection still proves its scoped state.
    assert label['conclusion']=='VERIFIED_WITHIN_SCOPE'

def test_runtime_failures_are_counted_without_leaking_exception_text(tmp_path):
    generate(tmp_path/'suite',count=1)
    class Broken:
        name='broken'
        def predict(self,raw):raise RuntimeError('potentially sensitive provider payload')
    report=evaluate(tmp_path/'suite',Broken())
    assert report['summary']['runtime_error_cases']==1
    assert report['summary']['conclusion_accuracy']==0
    assert 'sensitive' not in json.dumps(report)
