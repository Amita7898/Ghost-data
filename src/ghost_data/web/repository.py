"""SQLite repository. All evidence paths are opaque server-generated keys."""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ..execution import TERMINAL_STATUSES


def now():
    return datetime.now(UTC).isoformat()


def elapsed(created_at):
    return max(
        0.0,
        (datetime.now(UTC) - datetime.fromisoformat(created_at)).total_seconds(),
    )


def new_id():
    return str(uuid4())


class IntegrityFailure(ValueError):
    pass


class Repository:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.files = self.root / "evidence"
        self.files.mkdir(exist_ok=True, mode=0o700)
        self.db = self.root / "web.sqlite"
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS investigations(id TEXT PRIMARY KEY,title TEXT NOT NULL,subject_label TEXT NOT NULL,audit_at TEXT,scope TEXT,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY,investigation_id TEXT NOT NULL REFERENCES investigations(id),filename TEXT NOT NULL,sha256 TEXT NOT NULL,size INTEGER NOT NULL,source TEXT NOT NULL,created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS web_runs(id TEXT PRIMARY KEY,investigation_id TEXT NOT NULL REFERENCES investigations(id),artifact_id TEXT NOT NULL REFERENCES artifacts(id),mode TEXT NOT NULL,status TEXT NOT NULL,recorded_status TEXT,created_at TEXT NOT NULL,finished_at TEXT,conclusion TEXT,error TEXT,model TEXT NOT NULL,usage TEXT,report TEXT,limits TEXT NOT NULL,trace TEXT,idempotency TEXT UNIQUE);
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_live ON web_runs((1)) WHERE mode='live' AND status IN ('queued','running','cancelling');
            CREATE TABLE IF NOT EXISTS web_events(run_id TEXT NOT NULL REFERENCES web_runs(id),seq INTEGER NOT NULL,elapsed_seconds REAL NOT NULL,kind TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(run_id,seq));
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=5)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            with db:
                yield db
        finally:
            db.close()

    def investigation(self, id):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM investigations WHERE id=?", (str(id),)
            ).fetchone()
            if row is None:
                raise KeyError("Investigation not found")
            value = dict(row)
            value["scope"] = json.loads(value["scope"]) if value["scope"] else None
            value["evidence_count"] = db.execute(
                "SELECT COUNT(*) FROM artifacts WHERE investigation_id=?", (str(id),)
            ).fetchone()[0]
            latest = db.execute(
                "SELECT id,status,mode,conclusion,created_at FROM web_runs WHERE investigation_id=? ORDER BY created_at DESC LIMIT 1",
                (str(id),),
            ).fetchone()
            value["latest_run"] = dict(latest) if latest else None
            return value

    def investigations(self):
        with self.connect() as db:
            ids = [
                r[0]
                for r in db.execute(
                    "SELECT id FROM investigations ORDER BY created_at DESC"
                )
            ]
        return [self.investigation(id) for id in ids]

    def create(self, data):
        id = new_id()
        with self.connect() as db:
            db.execute(
                "INSERT INTO investigations VALUES (?,?,?,?,?,?)",
                (
                    id,
                    data.title,
                    data.subject_label,
                    data.audit_at.isoformat() if data.audit_at else None,
                    json.dumps(data.scope) if data.scope is not None else None,
                    now(),
                ),
            )
        return self.investigation(id)

    def artifacts(self, id):
        self.investigation(id)
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM artifacts WHERE investigation_id=? ORDER BY created_at",
                    (str(id),),
                )
            ]

    def artifact(self, id):
        with self.connect() as db:
            r = db.execute("SELECT * FROM artifacts WHERE id=?", (str(id),)).fetchone()
        if r is None:
            raise KeyError("Artifact not found")
        return dict(r)

    def path(self, id):
        self.artifact(id)
        path = self.files / (str(id) + ".json")
        if path.is_symlink() or path.resolve().parent != self.files.resolve():
            raise IntegrityFailure("Unsafe evidence path")
        return path

    def read(self, id):

        artifact = self.artifact(id)
        try:
            with self.path(id).open("rb") as stream:
                raw = stream.read(5_000_001)
        except OSError:
            raise IntegrityFailure("Registered evidence is unavailable") from None
        if (
            len(raw) != artifact["size"]
            or hashlib.sha256(raw).hexdigest() != artifact["sha256"]
        ):
            raise IntegrityFailure("Registered evidence integrity check failed")
        return raw

    def store(self, investigation_id, raw, filename, source="upload"):

        self.investigation(investigation_id)
        id = new_id()
        digest = hashlib.sha256(raw).hexdigest()
        path = self.files / (id + ".json")
        with path.open("xb") as f:
            f.write(raw)
        try:
            with self.connect() as db:
                db.execute(
                    "INSERT INTO artifacts VALUES (?,?,?,?,?,?,?)",
                    (
                        id,
                        str(investigation_id),
                        filename,
                        digest,
                        len(raw),
                        source,
                        now(),
                    ),
                )
        except Exception:
            path.unlink()
            raise
        return self.artifact(id)

    def run(self, id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM web_runs WHERE id=?", (str(id),)).fetchone()
        if row is None:
            raise KeyError("Run not found")
        r = dict(row)
        for k in ("usage", "report", "limits"):
            r[k] = json.loads(r[k]) if r[k] else None
        r.pop("trace", None)
        r.pop("idempotency", None)
        return r

    def runs(self, investigation_id=None):
        with self.connect() as db:
            rows = db.execute(
                "SELECT id FROM web_runs"
                + (" WHERE investigation_id=?" if investigation_id else "")
                + " ORDER BY created_at DESC",
                (str(investigation_id),) if investigation_id else (),
            ).fetchall()
        return [self.run(r[0]) for r in rows]

    def start(self, investigation_id, artifact_id, mode, model, limits, key=None):
        self.investigation(investigation_id)
        a = self.artifact(artifact_id)
        if a["investigation_id"] != str(investigation_id):
            raise ValueError("Artifact does not belong to investigation")
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if key:
                existing = db.execute(
                    "SELECT id,investigation_id,artifact_id,limits FROM web_runs WHERE idempotency=?",
                    (key,),
                ).fetchone()
                if existing:
                    if (
                        existing["investigation_id"],
                        existing["artifact_id"],
                        existing["limits"],
                    ) != (
                        str(investigation_id),
                        str(artifact_id),
                        json.dumps(limits, sort_keys=True),
                    ):
                        raise ValueError(
                            "Idempotency key reused with different request"
                        )
                    return self.run(existing["id"]), False
            id = new_id()
            db.execute(
                "INSERT INTO web_runs(id,investigation_id,artifact_id,mode,status,created_at,model,limits,idempotency) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    id,
                    str(investigation_id),
                    str(artifact_id),
                    mode,
                    "queued",
                    now(),
                    model,
                    json.dumps(limits, sort_keys=True),
                    key,
                ),
            )
        return self.run(id), True

    def update(self, id, **fields):
        permitted = {
            "status",
            "finished_at",
            "conclusion",
            "error",
            "usage",
            "report",
            "trace",
            "recorded_status",
        }
        if not set(fields) <= permitted:
            raise ValueError("Invalid run update")
        values = [
            json.dumps(v) if k in ("usage", "report", "trace") and v is not None else v
            for k, v in fields.items()
        ]
        with self.connect() as db:
            db.execute(
                "UPDATE web_runs SET "
                + ",".join(k + "=?" for k in fields)
                + " WHERE id=?",
                (*values, str(id)),
            )

    def event(self, id, event):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            state = db.execute(
                "SELECT status,created_at FROM web_runs WHERE id=?", (str(id),)
            ).fetchone()
            if (
                state
                and state["status"] in TERMINAL_STATUSES
                and event["kind"] != "execution_interrupted"
            ):
                return
            seq = db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM web_events WHERE run_id=?",
                (str(id),),
            ).fetchone()[0]
            db.execute(
                "INSERT INTO web_events VALUES(?,?,?,?,?)",
                (
                    str(id),
                    seq,
                    event.get("elapsed_seconds", elapsed(state["created_at"])),
                    event["kind"],
                    json.dumps(event["data"]),
                ),
            )

    def events(self, id, after=0):
        with self.connect() as db:
            rows = db.execute(
                "SELECT seq,elapsed_seconds,kind,data FROM web_events WHERE run_id=? AND seq>? ORDER BY seq",
                (str(id), after),
            ).fetchall()
        return [dict(r) | {"data": json.loads(r["data"])} for r in rows]

    def recover(self):
        with self.connect() as db:
            ids = [
                r[0]
                for r in db.execute(
                    "SELECT id FROM web_runs WHERE status IN ('queued','running','cancelling')"
                )
            ]
            db.execute(
                "UPDATE web_runs SET status='interrupted',finished_at=?,error='Backend restarted before run completed' WHERE status IN ('queued','running','cancelling')",
                (now(),),
            )
        for id in ids:
            self.event(
                id,
                {
                    "kind": "execution_interrupted",
                    "data": {
                        "message": "Backend restarted; recorded progress preserved"
                    },
                },
            )

    def mark_running(self, id):
        with self.connect() as db:
            return (
                db.execute(
                    "UPDATE web_runs SET status='running' WHERE id=? AND status='queued'",
                    (str(id),),
                ).rowcount
                == 1
            )

    def request_cancel(self, id):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            r = db.execute(
                "SELECT status,mode,created_at FROM web_runs WHERE id=?", (str(id),)
            ).fetchone()
            if not r:
                raise KeyError(id)
            if r["mode"] != "live":
                raise ValueError(
                    "Pause replay in the browser; it does not run inference"
                )
            if r["status"] in ("queued", "running"):
                db.execute(
                    "UPDATE web_runs SET status='cancelling' WHERE id=?", (str(id),)
                )
                seq = db.execute(
                    "SELECT COALESCE(MAX(seq),0)+1 FROM web_events WHERE run_id=?",
                    (str(id),),
                ).fetchone()[0]
                db.execute(
                    "INSERT INTO web_events VALUES(?,?,?,?,?)",
                    (
                        str(id),
                        seq,
                        elapsed(r["created_at"]),
                        "cancellation_requested",
                        json.dumps(
                            {"message": "Waiting for the bounded in-flight call"}
                        ),
                    ),
                )
        return self.run(id)

    def finish(self, id, **fields):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT status,created_at FROM web_runs WHERE id=?", (str(id),)
            ).fetchone()
            if current["status"] in TERMINAL_STATUSES:
                return
            if (
                current["status"] == "cancelling"
                and fields["status"] != "verification_failed"
            ):
                fields["status"] = "cancelled"
            values = [
                json.dumps(v)
                if k in ("usage", "report", "trace") and v is not None
                else v
                for k, v in fields.items()
            ]
            db.execute(
                "UPDATE web_runs SET "
                + ",".join(k + "=?" for k in fields)
                + " WHERE id=?",
                (*values, str(id)),
            )
            seq = db.execute(
                "SELECT COALESCE(MAX(seq),0)+1 FROM web_events WHERE run_id=?",
                (str(id),),
            ).fetchone()[0]
            db.execute(
                "INSERT INTO web_events VALUES(?,?,?,?,?)",
                (
                    str(id),
                    seq,
                    elapsed(current["created_at"]),
                    "execution_finished",
                    json.dumps(
                        {"status": fields["status"], "message": fields.get("error")}
                    ),
                ),
            )
