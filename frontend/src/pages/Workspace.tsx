import {
  ArrowLeft,
  Cpu,
  Database,
  FileJson,
  FolderSearch,
  Loader2,
  Pause,
  Play,
  Radio,
  ShieldCheck,
  Square,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  api,
  base,
  date,
  human,
  mergeEvents,
  terminal,
  type Artifact,
  type Context,
  type Event,
  type Investigation,
  type Run,
  type Runtime,
} from "../api";
import {
  Badge,
  Empty,
  ErrorBox,
  EventCard,
  ResultPanel,
  SourceViewer,
} from "../components";

export default function Workspace({ runtime }: { runtime: Runtime | null }) {
  const { id } = useParams();
  const [params, setParams] = useSearchParams();
  const [inv, setInv] = useState<Investigation | null>(null);
  const [context, setContext] = useState<Context | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [inputArtifact, setInputArtifact] = useState("");
  const [runs, setRuns] = useState<Run[]>([]);
  const [run, setRun] = useState<Run | null>(null);
  const [eventState, setEventState] = useState<{ id: string; rows: Event[] }>({
    id: "",
    rows: [],
  });
  const activeRun = useRef("");
  activeRun.current = run?.id || "";
  const events = eventState.id === (run?.id || "") ? eventState.rows : [];
  function setEvents(update: Event[] | ((old: Event[]) => Event[])) {
    const owner = run?.id || "";
    setEventState((old) =>
      activeRun.current !== owner
        ? old
        : {
            id: owner,
            rows:
              typeof update === "function"
                ? update(old.id === owner ? old.rows : [])
                : update,
          },
    );
  }
  const refreshVersion = useRef(0);
  const [error, setError] = useState("");
  const [source, setSource] = useState("");
  const [starting, setStarting] = useState(false);
  const [connection, setConnection] = useState("");
  const [cursor, setCursor] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(4);
  const tail = useRef<HTMLDivElement>(null);
  const playbackReady = useRef<string | null>(null);
  const selected = params.get("run");
  const refresh = useCallback(async () => {
    if (!id) return;
    const version = ++refreshVersion.current;
    const [i, a, r] = await Promise.all([
      api<Investigation>(`/investigations/${id}`),
      api<Artifact[]>(`/investigations/${id}/evidence`),
      api<Run[]>(`/investigations/${id}/runs`),
    ]);
    const chosen = r.find((x) => x.id === selected) || r[0] || null;
    const ctx = await api<Context>(
      `/investigations/${id}/context${chosen ? "?artifact_id=" + chosen.artifact_id : ""}`,
    );
    if (version !== refreshVersion.current) return;
    setInv(i);
    setArtifacts(a);
    setInputArtifact(a.at(-1)?.id || "");
    setRuns(r);
    setRun(chosen);
    setContext(ctx);
  }, [id, selected]);
  useEffect(() => {
    if (inv?.id !== id) {
      setInv(null);
      setRun(null);
      setContext(null);
    }
    setEvents([]);
    refresh().catch((e) => setError(e.message));
    return () => {
      refreshVersion.current++;
    };
  }, [refresh]);
  useEffect(() => {
    if (!run) return;
    playbackReady.current = null;
    let closed = false;
    let es: EventSource | undefined;
    api<Event[]>(`/runs/${run.id}/events`)
      .then((initial) => {
        if (closed) return;
        setEvents((old) => mergeEvents(old, initial));
        if (run.mode === "replay") {
          const saved = localStorage.getItem("ghost-replay-" + run.id);
          const restored = Number(saved);
          setCursor(
            saved && Number.isFinite(restored)
              ? Math.min(Math.max(0, restored), initial.length)
              : params.get("replay") === "1"
                ? 0
                : initial.length,
          );
          playbackReady.current = run.id;
          setPlaying(!saved && params.get("replay") === "1");
          setConnection("Recorded events");
          return;
        }
        if (terminal(run)) {
          setConnection("Saved events");
          return;
        }
        es = new EventSource(
          `${base}/runs/${run.id}/stream?after=${initial.at(-1)?.seq || 0}`,
        );
        es.onopen = () => {
          if (!closed) setConnection("Live connection");
        };
        es.addEventListener("activity", (message) => {
          if (closed) return;
          const item = JSON.parse((message as MessageEvent).data) as Event;
          setEvents((old) => mergeEvents(old, [item]));
        });
        es.addEventListener("end", () => {
          if (closed) return;
          es?.close();
          setConnection("Saved events");
          api<Run>("/runs/" + run.id)
            .then((value) => {
              if (closed) return;
              setRun(value);
              setRuns((old) => old.map((r) => (r.id === value.id ? value : r)));
            })
            .catch((e) => setError(e.message));
        });
        es.onerror = () => {
          if (!closed) setConnection("Reconnecting — progress is preserved");
        };
      })
      .catch((e) => setError(e.message));
    return () => {
      closed = true;
      es?.close();
    };
  }, [run?.id]);
  useEffect(() => {
    if (!run || run.mode !== "replay" || !playing) return;
    const timer = setInterval(
      () => setCursor((old) => Math.min(old + 1, events.length)),
      1000 / speed,
    );
    return () => clearInterval(timer);
  }, [playing, speed, events.length, run?.id]);
  useEffect(() => {
    if (
      run?.mode === "replay" &&
      playbackReady.current === run.id &&
      events.length > 0
    ) {
      localStorage.setItem("ghost-replay-" + run.id, String(cursor));
      if (cursor >= events.length && events.length) setPlaying(false);
    }
  }, [cursor, events.length, run?.id]);
  const shown = run?.mode === "replay" ? events.slice(0, cursor) : events;
  useEffect(() => {
    if (run?.status === "running" || playing)
      tail.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [shown.length]);
  async function start() {
    if (!context?.artifact) return;
    setStarting(true);
    setError("");
    try {
      const value = await api<Run>(`/investigations/${id}/runs`, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({
          artifact_id: inputArtifact || context.artifact.id,
        }),
      });
      setEvents([]);
      setRun(value);
      setParams({ run: value.id });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setStarting(false);
    }
  }
  async function cancel() {
    if (!run) return;
    try {
      setRun(await api<Run>(`/runs/${run.id}/cancel`, { method: "POST" }));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const selectEvidence = (evidenceId: string) => {
    const index =
      context?.bundle?.observations.findIndex((o) => o.id === evidenceId) ?? -1;
    if (index >= 0 && context?.artifact)
      setSource(`sha256:${context.artifact.sha256}#/observations/${index}`);
  };
  if (!inv)
    return (
      <div className="page">
        {error ? (
          <ErrorBox message={error} />
        ) : (
          <p className="loading">
            <Loader2 className="spin" />
            Loading investigation…
          </p>
        )}
      </div>
    );
  const active = !!run && !terminal(run);
  const latestModel = shown.filter((e) => e.kind === "model_requested").length;
  return (
    <div className="page workspace-page">
      <Link className="back-link" to="/">
        <ArrowLeft size={14} />
        Investigations
      </Link>
      <div className="workspace-heading">
        <div>
          <span className="eyebrow">AI INVESTIGATION WORKSPACE</span>
          <h1>{inv.title}</h1>
          <p>
            {context?.subject || inv.subject_label || "Identity pending"}{" "}
            <span className="separator">/</span>{" "}
            {context?.bundle?.request.audit_at
              ? date(context.bundle.request.audit_at) + " cutoff"
              : "No evidence uploaded"}
          </p>
        </div>
        <div className="workspace-actions">
          {run && <Badge value={run.mode} mode />}
          {run && <Badge value={run.status} />}
          <Link
            className="button secondary"
            to={`/investigations/${id}/evidence`}
          >
            <FolderSearch size={15} />
            Evidence
          </Link>
          {active ? (
            <button
              className="button danger"
              disabled={run?.status === "cancelling"}
              onClick={cancel}
            >
              <Square size={13} />
              {run?.status === "cancelling" ? "Cancelling…" : "Cancel run"}
            </button>
          ) : (
            <button
              className="button primary"
              disabled={starting || !context?.artifact || !runtime?.available}
              title={runtime?.message || "Checking local model"}
              onClick={start}
            >
              {starting ? (
                <Loader2 className="spin" size={15} />
              ) : (
                <Play size={15} />
              )}
              {run &&
              [
                "failed",
                "cancelled",
                "interrupted",
                "verification_failed",
              ].includes(run.status)
                ? "Retry live"
                : "Start live"}
            </button>
          )}
        </div>
      </div>
      {error && <ErrorBox message={error} />}{" "}
      {runtime && !runtime.available && (
        <div className="offline-notice">
          <Cpu size={15} />
          <span>{runtime.message}</span>
        </div>
      )}
      <div className="workspace-grid">
        <aside className="context-column">
          <div className="section-heading">
            <FolderSearch size={15} />
            <h2>Investigation context</h2>
          </div>
          <section className="panel">
            <span className="eyebrow">SUBJECT</span>
            <h3 className="subject-name">
              {context?.subject || "Unresolved identity"}
            </h3>
            <span className="muted wrap">
              {context?.bundle?.request.identifier.value || inv.subject_label}
            </span>
            <div className="mini-divider" />
            <span className="eyebrow">EXACT AUDIT CUTOFF</span>
            <code className="wrap">
              {context?.bundle?.request.audit_at || "Not configured"}
            </code>
            <div className="mini-divider" />
            <span className="eyebrow">AUTHORIZATION SOURCE</span>
            <p className="request-quote">
              “{context?.bundle?.request.text || "Upload a supported bundle."}”
            </p>
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h3>Resource scope</h3>
              <span className="count">
                {context?.bundle?.targets.length || 0}
              </span>
            </div>
            {context?.bundle?.targets.map((t) => (
              <div className="resource-item" key={t.system + t.resource}>
                <Database size={14} />
                <div>
                  <code>{t.resource}</code>
                  <small>{t.system}</small>
                </div>
              </div>
            ))}
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h3>Evidence inventory</h3>
              <span className="count">{artifacts.length}</span>
            </div>
            {artifacts.map((a) => (
              <button
                className="evidence-item"
                key={a.id}
                onClick={() => setSource(a.sha256)}
              >
                <FileJson size={16} />
                <span>
                  {a.filename}
                  <small>
                    {(a.size / 1024).toFixed(1)} KB · {a.source}
                  </small>
                </span>
              </button>
            ))}
          </section>
          <section className="panel">
            <span className="eyebrow">POLICY</span>
            <p>Embedded evidence rules</p>
            <small className="muted">
              {context?.bundle?.rules.length || 0} categories · deterministic
              enforcement
            </small>
          </section>
          <section className="panel">
            <span className="eyebrow">NEXT LIVE INPUT</span>
            <select
              aria-label="Evidence bundle for next live run"
              className="input-selector"
              value={inputArtifact}
              onChange={(e) => setInputArtifact(e.target.value)}
            >
              {artifacts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.filename}
                </option>
              ))}
            </select>
            <p className="fine-print">
              Historical results keep their original source.
            </p>
          </section>
          <section className="panel">
            <span className="eyebrow">UNRESOLVED QUESTIONS</span>
            {run?.report ? (
              <>
                {run.report.unresolved.length ? (
                  <ul className="question-list">
                    {run.report.unresolved.slice(0, 5).map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="fine-print">
                    No unresolved questions recorded in this assessment.
                  </p>
                )}
              </>
            ) : (
              <p className="fine-print">Awaiting the validated assessment.</p>
            )}
          </section>
          <section className="panel compact-panel">
            <Cpu size={16} />
            <p>
              {run?.model || runtime?.model || "Local model"}
              <small>
                {run?.mode === "replay"
                  ? "Recorded model · no inference"
                  : "Runs on your machine"}
              </small>
            </p>
          </section>
        </aside>
        <section className="activity-column">
          <div className="section-heading">
            <div className="activity-heading">
              <Radio size={15} />
              <h2>Investigation activity</h2>
            </div>
            <span className="connection-label">{connection || "Ready"}</span>
          </div>
          {run?.mode === "replay" && (
            <div className="replay-bar">
              <span>
                <Play size={13} />
                RECORDED REPLAY
              </span>
              <button
                aria-label={playing ? "Pause replay" : "Play replay"}
                className="icon-button"
                onClick={() => {
                  if (cursor >= events.length) setCursor(0);
                  setPlaying(!playing);
                }}
              >
                {playing ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <select
                aria-label="Replay speed"
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
              >
                <option value={1}>1 event/s</option>
                <option value={2}>2 events/s</option>
                <option value={4}>4 events/s</option>
              </select>
              <button
                className="text-link"
                onClick={() => {
                  setCursor(events.length);
                  setPlaying(false);
                }}
              >
                Show all
              </button>
              <small>
                {Math.min(cursor, events.length)} / {events.length}
              </small>
            </div>
          )}
          {run?.mode === "replay" && (
            <p className="replay-note">
              Actual recorded events. Accelerated playback; timestamps are
              preserved. No model is running for this replay.
            </p>
          )}
          {run && (
            <div className="run-metrics">
              <span>
                {run.mode === "replay" ? "Recording totals" : "Reported usage"}
              </span>
              <strong>
                {Number(
                  run.usage?.model_calls ??
                    shown.filter((e) => e.kind === "model_requested").length,
                )}{" "}
                model turns
              </strong>
              <span>
                {(
                  ((run.usage?.input_tokens as number) || 0) +
                    ((run.usage?.output_tokens as number) || 0) ||
                  shown
                    .filter((e) => e.kind === "model_completed")
                    .reduce(
                      (n, e) =>
                        n +
                        Number(e.data.prompt_tokens || 0) +
                        Number(e.data.output_tokens || 0),
                      0,
                    )
                ).toLocaleString()}{" "}
                tokens
              </span>
              <span>{String(run.limits.turns || 6)} turn limit</span>
            </div>
          )}
          {runs.length > 1 && (
            <label className="run-selector">
              Run{" "}
              <select
                aria-label="Select investigation run"
                value={run?.id || ""}
                onChange={(e) => {
                  setEvents([]);
                  setParams({ run: e.target.value });
                }}
              >
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.mode.toUpperCase()} · {human(r.status)} ·{" "}
                    {date(r.created_at)}
                  </option>
                ))}
              </select>
            </label>
          )}
          <div className="timeline" aria-label="Investigation event timeline">
            {shown.length ? (
              shown.map((e) => (
                <EventCard key={e.seq} event={e} onSource={setSource} />
              ))
            ) : (
              <Empty
                title={
                  run?.mode === "replay"
                    ? "Recording ready"
                    : "Ready to investigate"
                }
              >
                {run?.mode === "replay"
                  ? "Play the genuine investigation or choose Show all."
                  : "Start a live local-model run to inspect evidence and validate hypotheses."}
              </Empty>
            )}
            {active && (
              <div className="live-waiting">
                <Loader2 size={17} className="spin" />
                <div>
                  <strong>
                    {run?.status === "cancelling"
                      ? "Cancellation requested"
                      : "Local investigation in progress"}
                  </strong>
                  <p>
                    {run?.status === "cancelling"
                      ? "The current model request is bounded by its timeout."
                      : "Model calls can take several minutes. Progress is saved; you can safely reload."}
                  </p>
                  <small>
                    {latestModel} model requests observed ·{" "}
                    {shown.filter((e) => e.kind === "tool_requested").length}{" "}
                    tool calls
                  </small>
                </div>
              </div>
            )}
            {run?.error && <ErrorBox message={run.error} />}
            <div ref={tail} />
          </div>
          <footer className="activity-footer">
            <ShieldCheck size={14} />
            <span>
              Observable actions only. Private chain-of-thought is never
              displayed.
            </span>
          </footer>
        </section>
        <ResultPanel run={run} onEvidence={selectEvidence} />
      </div>
      {source && (
        <SourceViewer
          artifacts={artifacts}
          source={source}
          onClose={() => setSource("")}
        />
      )}
    </div>
  );
}
