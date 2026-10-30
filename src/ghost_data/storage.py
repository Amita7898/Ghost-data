"""Local SQLite run repository. No model calls or evidence execution."""
import sqlite3
import hashlib
from datetime import datetime, timezone
from uuid import uuid4

class RunStore:
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, artifact BLOB NOT NULL, report TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS events (run_id TEXT NOT NULL REFERENCES runs(id), seq INTEGER NOT NULL, kind TEXT NOT NULL, detail TEXT NOT NULL, PRIMARY KEY(run_id,seq))')
            db.execute('PRAGMA user_version=1')

    def save(self, raw, report):
        if hashlib.sha256(raw).hexdigest() != report.artifact_sha256:
            raise ValueError('Report does not match artifact bytes')
        run_id = str(uuid4())
        with sqlite3.connect(self.path) as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('INSERT INTO runs VALUES (?,?,?,?)',(run_id,datetime.now(timezone.utc).isoformat(),raw,report.model_dump_json()))
            events = [('artifact_ingested',report.artifact_sha256),('authorization_assessed',report.authorization),
                      ('policy_assessed',str(len(report.assessments))),
                      ('validation_finished','rejected' if report.validation_errors else 'passed'),
                      ('audit_finished',report.conclusion)]
            db.executemany('INSERT INTO events VALUES (?,?,?,?)',[(run_id,n,k,d) for n,(k,d) in enumerate(events,1)])
        return run_id

    def read(self, run_id):
        with sqlite3.connect(self.path) as db:
            row = db.execute('SELECT report FROM runs WHERE id=?',(run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        return row[0]
