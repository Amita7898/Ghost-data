import copy
import json
from pathlib import Path
import pytest
from pydantic import ValidationError
from ghost_data.models import Bundle
from ghost_data.engine import audit
from ghost_data.authorization import classify
from ghost_data.verifier import check
from ghost_data.evidence import admission_reasons

@pytest.fixture
def data():
    return json.loads((Path(__file__).parents[1]/'examples/scoped_absence.json').read_text())

def run(data):return audit(Bundle.model_validate(data),'a'*64)

@pytest.mark.parametrize('field',['ingested_at','available_at','captured_at','observed_at'])
def test_late_timestamp_cannot_prove(data,field):
    data['observations'][0][field]='2026-01-21T12:00:00Z'
    if field=='observed_at':data['observations'][0]['captured_at']='2026-01-21T12:00:00Z'
    assert run(data).conclusion=='INCONCLUSIVE'

@pytest.mark.parametrize('field',['event_at','ingested_at','available_at','captured_at','observed_at'])
def test_exact_boundary_admitted(data,field):
    data['observations'][0][field]=data['request']['audit_at']
    assert run(data).conclusion=='VERIFIED_WITHIN_SCOPE'

def test_legacy_ingestion_and_forged_proposal(data):
    valid=run(data)
    data['observations'][0]['fields']={'ingested_at':'2026-01-21T00:00:00Z'}
    assert run(data).conclusion=='INCONCLUSIVE'
    assert check(Bundle.model_validate(data),valid)

def test_conflicting_legacy_timestamp_rejected(data):
    data['observations'][0].update(ingested_at='2026-01-20T12:00:00Z',fields={'ingested_at':'2026-01-21T12:00:00Z'})
    with pytest.raises(ValidationError):Bundle.model_validate(data)

def test_stricter_availability_cutoff(data):
    data['request']['evidence_cutoff']='2026-01-20T11:59:59Z'
    assert run(data).conclusion=='INCONCLUSIVE'

def test_inconsistent_ingestion_not_admitted(data):
    data['observations'][0]['ingested_at']='2026-01-19T12:00:00Z'
    assert run(data).conclusion=='INCONCLUSIVE'

def test_contradiction_cannot_be_selectively_removed(data):
    conflict=copy.deepcopy(data['observations'][0]);conflict.update(id='contradiction',state='PRESENT')
    data['observations'].append(conflict)
    assert run(data).conclusion=='INCONCLUSIVE'
    data['observations'][1]['ingested_at']='2026-01-21T12:00:00Z'
    assert run(data).conclusion=='VERIFIED_WITHIN_SCOPE'

def test_future_event_rejected(data):
    data['observations'][0]['event_at']='2026-01-21T12:00:00Z'
    with pytest.raises(ValidationError):Bundle.model_validate(data)

@pytest.mark.parametrize('text,expected',[
 ('Bitte löschen Sie mein Konto nicht.','DECLINED'),
 ('Bitte mein Konto niemals löschen.','DECLINED'),
 ('Mein Konto darf nicht gelöscht werden.','DECLINED'),
 ('Bitte mein Konto nicht nicht löschen.','AMBIGUOUS'),
 ('Bitte löschen Sie mein Konto.','AMBIGUOUS'),
 ('Ne supprimez pas mon compte.','DECLINED'),
 ('No borres mi cuenta.','DECLINED'),
 ('Do not erase my personal data.','DECLINED'),
 ('I do not want to cancel my deletion request.','AMBIGUOUS'),
 ('Please delete my account.','AUTHORIZED'),
 ('How do I delete my account?','AMBIGUOUS')])
def test_multilingual_negation(text,expected):assert classify(text)==expected

def test_ingestion_required_by_investigation_rule(data):
    data['request']['require_ingestion_time']=True
    assert run(data).conclusion=='INCONCLUSIVE'
    data['observations'][0]['ingested_at']=data['request']['audit_at']
    assert run(data).conclusion=='VERIFIED_WITHIN_SCOPE'
