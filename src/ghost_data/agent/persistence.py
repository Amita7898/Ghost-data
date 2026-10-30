"""Store the visible input, deterministic report and agent events atomically."""
import hashlib
import json
import sqlite3
from ..storage import RunStore

def save_investigation(path,raw,trace):
    if hashlib.sha256(raw).hexdigest()!=trace['artifact_sha256']:
        raise ValueError('Trace artifact hash mismatch')
    RunStore(path)  # Keep compatibility schema, add an independent event table.
    with sqlite3.connect(str(path)) as db:
        db.execute('CREATE TABLE IF NOT EXISTS agent_runs (id TEXT PRIMARY KEY, artifact BLOB NOT NULL, trace TEXT NOT NULL)')
        db.execute('INSERT INTO agent_runs VALUES (?,?,?)',(trace['investigation_id'],raw,json.dumps(trace)))
