"""Local-only API; no public upload surface or arbitrary filesystem tools."""

import asyncio
import hashlib
import html
import json
import os
import re
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from ..evidence import admission_reasons
from ..identity import subject_for_request
from ..models import Bundle
from .locking import exclusive_file
from .models import (
    Artifact,
    Context,
    CreateInvestigation,
    Demo,
    Error,
    Event,
    Investigation,
    Preview,
    Run,
    RuntimeStatus,
    StartRun,
)
from .repository import IntegrityFailure, Repository
from .service import EXAMPLES, MAX_BYTES, Service

TERMINAL = {"completed", "cancelled", "failed", "interrupted"}
ALLOWED_ORIGINS = {
    f"http://{host}:{port}"
    for host in ("127.0.0.1", "localhost")
    for port in (8000, 5173)
}


def markdown_text(value):
    text = html.escape(str(value), quote=False).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|])", r"\\\1", text)


def create_app(project_root=None, data_dir=None, runtime_factory=None, offline=None):
    root = Path(
        project_root or os.environ.get("GHOST_DATA_PROJECT", Path.cwd())
    ).resolve()
    offline = (
        os.environ.get("GHOST_DATA_OFFLINE") == "1" if offline is None else offline
    )
    repo = Repository(
        data_dir or os.environ.get("GHOST_DATA_DATA_DIR", root / ".localdata")
    )
    service = Service(repo, root, runtime_factory)

    @asynccontextmanager
    async def lifespan(app):
        with exclusive_file(repo.root / "api.lock"):
            repo.recover()
            try:
                yield
            finally:
                service.shutdown()

    app = FastAPI(
        title="Ghost Data Local Investigation API",
        version="0.4.0",
        lifespan=lifespan,
        responses={
            400: {"model": Error},
            404: {"model": Error},
            409: {"model": Error},
            422: {"model": Error},
        },
    )
    app.state.repo = repo
    app.state.service = service
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(ALLOWED_ORIGINS),
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=[
            "Content-Type",
            "X-Filename",
            "Idempotency-Key",
            "Last-Event-ID",
        ],
    )

    @app.middleware("http")
    async def local_guard(request, call_next):
        host = request.headers.get("host", "").split(":")[0]
        if host not in ("localhost", "127.0.0.1"):
            return JSONResponse(
                {"code": "HOST_DENIED", "message": "Localhost only"}, 403
            )
        origin = request.headers.get("origin")
        if (
            origin
            and origin not in ALLOWED_ORIGINS
            and origin != f"{request.url.scheme}://{request.headers.get('host', '')}"
        ):
            return JSONResponse(
                {"code": "ORIGIN_DENIED", "message": "Untrusted browser origin"}, 403
            )
        try:
            if int(request.headers.get("content-length", "0")) > MAX_BYTES + 10000:
                return JSONResponse(
                    {
                        "code": "UPLOAD_TOO_LARGE",
                        "message": "Maximum evidence size is 5 MB",
                    },
                    413,
                )
        except ValueError:
            return JSONResponse(
                {"code": "INVALID_LENGTH", "message": "Invalid Content-Length"}, 400
            )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        return JSONResponse(
            {"code": "NOT_FOUND", "message": "Requested resource not found"}, 404
        )

    @app.exception_handler(sqlite3.IntegrityError)
    async def conflict(request, exc):
        return JSONResponse(
            {
                "code": "LIVE_RUN_BUSY",
                "message": "A live investigation is already active. Wait or cancel it first.",
            },
            409,
        )

    @app.exception_handler(IntegrityFailure)
    async def integrity_error(request, exc):
        return JSONResponse(
            {
                "code": "INTEGRITY_ERROR",
                "message": "Registered evidence changed or is unavailable. Upload the original again.",
            },
            409,
        )

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        details = (
            [
                {"location": ".".join(map(str, e["loc"])), "message": e["msg"]}
                for e in exc.errors(include_input=False)
            ]
            if isinstance(exc, ValidationError)
            else []
        )
        return JSONResponse(
            {
                "code": "INVALID_EVIDENCE",
                "message": "Evidence or configuration is invalid"
                if details
                else str(exc),
                "details": details,
            },
            422,
        )

    @app.exception_handler(RequestValidationError)
    async def request_invalid(request, exc):
        return JSONResponse(
            {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request",
                "details": [
                    {"location": ".".join(map(str, e["loc"])), "message": e["msg"]}
                    for e in exc.errors()
                ],
            },
            422,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(
            {"code": "REQUEST_REJECTED", "message": str(exc.detail)}, exc.status_code
        )

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "local_only": True, "version": "0.4.0"}

    @app.get("/api/v1/runtime", response_model=RuntimeStatus)
    async def runtime():
        def inspect():
            if offline:
                return {
                    "available": False,
                    "model": "qwen3.5:latest",
                    "message": "Offline mode: live inference disabled. Recorded replay is ready.",
                }
            try:
                instance = service.runtime_factory()
                instance.timeout = 3
                instance.ready()
                return {
                    "available": True,
                    "model": instance.model,
                    "message": "Local model ready",
                }
            except Exception:  # noqa: BLE001 - readiness failure is reported, never success
                return {
                    "available": False,
                    "model": "qwen3.5:latest",
                    "message": "Start Ollama locally, then run ghost-data doctor. Replay remains available.",
                }

        return await asyncio.to_thread(inspect)

    @app.get("/api/v1/investigations", response_model=list[Investigation])
    def investigations():
        return repo.investigations()

    @app.post("/api/v1/investigations", response_model=Investigation, status_code=201)
    def create(body: CreateInvestigation):
        return repo.create(body)

    @app.get("/api/v1/investigations/{id}", response_model=Investigation)
    def investigation(id: UUID):
        return repo.investigation(id)

    @app.get("/api/v1/examples")
    def examples():
        return [{"id": key, "filename": value} for key, value in EXAMPLES.items()]

    @app.get("/api/v1/examples/{key}", response_model=Bundle)
    def example(key: str):
        if key not in EXAMPLES:
            raise KeyError(key)
        return json.loads((root / "examples" / EXAMPLES[key]).read_text())

    @app.put(
        "/api/v1/investigations/{id}/evidence",
        response_model=Artifact,
        status_code=201,
        openapi_extra={
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/Bundle"}
                    }
                },
            }
        },
    )
    async def upload(
        id: UUID, request: Request, x_filename: str = Header(default="evidence.json")
    ):
        repo.investigation(id)
        if (
            not re.fullmatch(r"[A-Za-z0-9 _.-]{1,100}", x_filename)
            or ".." in x_filename
            or not x_filename.lower().endswith(".json")
        ):
            raise HTTPException(
                400, "Use a plain .json filename; paths are not allowed"
            )
        if request.headers.get("content-type", "").split(";")[0] not in (
            "application/json",
            "application/octet-stream",
        ):
            raise HTTPException(
                415, "Only structured JSON evidence bundles are supported"
            )
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > MAX_BYTES:
                raise HTTPException(413, "Maximum evidence size is 5 MB")
        return await asyncio.to_thread(service.ingest, id, bytes(raw), x_filename)

    @app.get("/api/v1/investigations/{id}/evidence", response_model=list[Artifact])
    def artifacts(id: UUID):
        return repo.artifacts(id)

    @app.get("/api/v1/artifacts/{id}/content")
    def content(id: UUID):
        artifact = repo.artifact(id)
        raw = repo.read(id)
        if hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
            raise HTTPException(409, "Evidence integrity check failed")
        return Response(
            raw,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="evidence-{id}.json"'
            },
        )

    @app.get("/api/v1/artifacts/{id}/fragment", response_model=Preview)
    def fragment(id: UUID, pointer: str = Query(default="", max_length=240)):
        artifact = repo.artifact(id)
        raw = repo.read(id)
        if hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
            raise HTTPException(409, "Evidence integrity check failed")
        value = json.loads(raw)
        if pointer:
            if not re.fullmatch(
                r"/(observations|identities|targets|rules)/[0-9]+", pointer
            ):
                raise HTTPException(400, "Select a registered source row")
            section, index = pointer.strip("/").split("/")
            try:
                value = value[section][int(index)]
            except (IndexError, KeyError):
                raise KeyError("Source row not found")
        text = json.dumps(value, indent=2, ensure_ascii=False)
        return {
            "source": f"sha256:{artifact['sha256']}#{pointer}",
            "text": text[:20000],
            "truncated": len(text) > 20000,
        }

    @app.post("/api/v1/investigations/{id}/runs", response_model=Run, status_code=202)
    def start(
        id: UUID,
        body: StartRun,
        idempotency_key: str = Header(min_length=8, max_length=80),
    ):
        if offline:
            raise HTTPException(
                503, "Offline mode is enabled. Recorded replay remains available."
            )
        return service.start(id, body, idempotency_key)

    @app.get("/api/v1/runs", response_model=list[Run])
    def runs():
        return repo.runs()

    @app.get("/api/v1/investigations/{id}/runs", response_model=list[Run])
    def case_runs(id: UUID):
        repo.investigation(id)
        return repo.runs(id)

    @app.get("/api/v1/runs/{id}", response_model=Run)
    def run(id: UUID):
        return repo.run(id)

    @app.post("/api/v1/runs/{id}/cancel", response_model=Run)
    def cancel(id: UUID):
        return service.cancel(id)

    @app.get("/api/v1/runs/{id}/events", response_model=list[Event])
    def events(id: UUID, after: int = Query(default=0, ge=0)):
        repo.run(id)
        return repo.events(id, after)

    @app.get("/api/v1/runs/{id}/stream")
    async def stream(id: UUID, request: Request, after: int = Query(default=0, ge=0)):
        repo.run(id)
        try:
            cursor = max(after, int(request.headers.get("last-event-id", "0")))
        except ValueError:
            raise HTTPException(400, "Invalid event cursor")

        async def generate():
            nonlocal cursor
            while not await request.is_disconnected():
                rows = await asyncio.to_thread(repo.events, id, cursor)
                for event in rows:
                    cursor = event["seq"]
                    yield f"id: {cursor}\nevent: activity\ndata: {json.dumps(event)}\n\n"
                state = await asyncio.to_thread(repo.run, id)
                if state["status"] in TERMINAL:
                    # One extra read closes the race between event append and status commit.
                    tail = await asyncio.to_thread(repo.events, id, cursor)
                    for event in tail:
                        cursor = event["seq"]
                        yield f"id: {cursor}\nevent: activity\ndata: {json.dumps(event)}\n\n"
                    yield "event: end\ndata: {}\n\n"
                    break
                yield ": keepalive\n\n"
                await asyncio.sleep(0.4)

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/v1/demos", response_model=list[Demo])
    def demos():
        return service.demos()

    @app.post("/api/v1/demos/{key}/open", response_model=Run, status_code=201)
    def open_demo(key: str):
        return service.open_demo(key)

    @app.get("/api/v1/investigations/{id}/context", response_model=Context)
    def context(id: UUID, artifact_id: UUID | None = None):
        inv = repo.investigation(id)
        artifacts = repo.artifacts(id)
        artifact = (
            repo.artifact(artifact_id)
            if artifact_id
            else artifacts[-1]
            if artifacts
            else None
        )
        if artifact is None:
            return {"investigation": inv, "bundle": None, "relationships": []}
        if artifact["investigation_id"] != str(id):
            raise KeyError("Wrong investigation")
        bundle, digest = service.parse(repo.read(artifact["id"]))
        if digest != artifact["sha256"]:
            raise HTTPException(409, "Evidence integrity check failed")
        subject = subject_for_request(bundle)
        links = []
        eligibility = {}
        for index, o in enumerate(bundle.observations):
            t = next((t for t in bundle.targets if t.key == o.key), None)
            reasons = (
                list(admission_reasons(bundle, o, t, subject))
                if t and subject
                else ["identity_unresolved" if not subject else "outside_scope"]
            )
            eligibility[o.id] = reasons
            if not reasons:
                links.append(
                    {
                        "from": subject,
                        "to": o.system + "/" + o.resource,
                        "label": "source-backed identity",
                        "evidence_id": o.id,
                        "source": f"sha256:{digest}#/observations/{index}",
                    }
                )
        return {
            "investigation": inv,
            "bundle": bundle.model_dump(mode="json"),
            "artifact": artifact,
            "subject": subject,
            "relationships": links,
            "eligibility": eligibility,
        }

    @app.get("/api/v1/runs/{id}/report")
    def report(id: UUID):
        run = repo.run(id)
        value = run["report"]
        lines = [
            "# Ghost Data investigation report",
            "",
            f"Mode: {run['mode'].upper()}",
            f"Execution: {run['status']}",
            f"Conclusion: {run['conclusion'] or 'Not available'}",
            "",
        ]
        if value:
            for a in value["assessments"]:
                lines.extend(
                    [
                        f"- {markdown_text(a['system'])} / {markdown_text(a['resource'])}: {a['status']} — {markdown_text(a['reason'])}",
                        f"  Sources: {', '.join(markdown_text(e) for e in a['evidence']) or 'none'}",
                    ]
                )
            lines += [
                "",
                "## Unresolved questions",
                *["- " + markdown_text(x) for x in value["unresolved"]],
                "",
                "## Recommended actions",
                *[
                    "- " + markdown_text(json.dumps(x))
                    for x in value["recommendations"]
                ],
            ]
        if run["error"]:
            lines += ["", "Error: " + run["error"]]
        return Response(
            "\n".join(lines) + "\n",
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="ghost-data-{id}.md"'
            },
        )

    dist = root / "frontend/dist"
    if (dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/") or not (dist / "index.html").exists():
            raise HTTPException(404, "Not found")
        return FileResponse(dist / "index.html")

    return app
