import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  FileJson,
  GitBranch,
  Loader2,
  ShieldCheck,
  Terminal,
  X,
} from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  api,
  base,
  human,
  parseSource,
  type Artifact,
  type Event,
  type Run,
} from "./api";
export function Badge({ value, mode }: { value: string; mode?: boolean }) {
  const tone = mode
    ? value === "replay"
      ? "amber"
      : "purple"
    : ["completed", "SATISFIED", "VERIFIED_WITHIN_SCOPE", "accepted"].includes(
          value,
        )
      ? "green"
      : [
            "failed",
            "verification_failed",
            "VIOLATED",
            "NON_COMPLIANT",
            "rejected",
          ].includes(value)
        ? "red"
        : ["running", "queued"].includes(value)
          ? "purple"
          : "amber";
  return (
    <span className={`badge ${tone}`}>
      {value === "running" && <span className="pulse-dot" />}
      {human(value)}
    </span>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <FileJson size={28} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="error-box" role="alert">
      <AlertTriangle size={16} />
      <span>{message}</span>
    </div>
  );
}
export function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    (ref.current?.querySelector<HTMLElement>("button") || ref.current)?.focus();
    function key(e: KeyboardEvent) {
      if (e.key === "Escape") closeRef.current();
      if (e.key === "Tab") {
        const nodes = ref.current?.querySelectorAll<HTMLElement>(
          'button,a,input,select,[tabindex="0"]',
        );
        if (!nodes?.length) return;
        const first = nodes[0],
          last = nodes[nodes.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
        if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      if (previous?.isConnected) previous.focus();
    };
  }, []);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={ref}
        tabIndex={-1}
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <header>
          <div>
            <span className="eyebrow">SOURCE INSPECTOR</span>
            <h2>{title}</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Close evidence inspector"
            onClick={onClose}
          >
            <X size={20} />
          </button>
        </header>
        {children}
      </div>
    </div>
  );
}
export function SourceViewer({
  artifacts,
  source,
  onClose,
}: {
  artifacts: Artifact[];
  source: string;
  onClose: () => void;
}) {
  const [preview, setPreview] = useState<{
    text: string;
    source: string;
    truncated: boolean;
  } | null>(null);
  const [error, setError] = useState("");
  const parsed = parseSource(source);
  const artifact = artifacts.find((a) => a.sha256 === (parsed?.sha || source));
  useEffect(() => {
    setPreview(null);
    setError("");
    if (!artifact) {
      setError("This source is not registered in the investigation.");
      return;
    }
    api<{ text: string; source: string; truncated: boolean }>(
      `/artifacts/${artifact.id}/fragment?pointer=${encodeURIComponent(parsed?.pointer || "")}`,
    )
      .then(setPreview)
      .catch((e) => setError(e.message));
  }, [artifact?.id, source]);
  return (
    <Modal title={artifact?.filename || "Evidence source"} onClose={onClose}>
      <div className="source-meta">
        <FileJson size={16} />
        <code>{parsed?.pointer || "Original JSON bundle"}</code>
        {artifact && (
          <a
            className="text-link"
            href={`${base}/artifacts/${artifact.id}/content`}
          >
            Download original <ArrowUpRight size={14} />
          </a>
        )}
      </div>
      {error ? (
        <ErrorBox message={error} />
      ) : preview ? (
        <>
          <pre className="source-code">{preview.text}</pre>
          {preview.truncated && (
            <p className="muted">
              Preview truncated at 20,000 characters. Download the original for
              full content.
            </p>
          )}
          <footer className="hash">
            <ShieldCheck size={14} />
            <code>{preview.source}</code>
          </footer>
        </>
      ) : (
        <p className="loading">
          <Loader2 className="spin" size={16} />
          Loading registered source…
        </p>
      )}
    </Modal>
  );
}
const eventNames: Record<string, string> = {
  investigation_started: "Investigation started",
  model_requested: "Local model investigating",
  model_completed: "Model response received",
  tool_requested: "Tool selected by model",
  tool_returned: "Evidence tool returned",
  hypothesis_validated: "Hypothesis checked",
  model_summary: "Model decision summary",
  follow_up_proposed: "Suggested follow-up · experimental",
  deterministic_conclusion: "Independent audit assessment",
  verification_failed: "Evidence verification failed",
  runtime_ready: "Local model ready",
  run_queued: "Investigation admitted",
  run_started: "Live execution started",
  execution_finished: "Execution finished",
  completion_rejected: "Response schema rejected",
  cancellation_requested: "Cancellation requested",
  execution_interrupted: "Execution interrupted",
  error: "Runtime error",
};
export function EventCard({
  event,
  onSource,
}: {
  event: Event;
  onSource: (s: string) => void;
}) {
  const d = event.data as Record<string, any>;
  const [expanded, setExpanded] = useState(false);
  const decision = event.kind === "hypothesis_validated";
  const accepted = d.result?.accepted;
  const source = d.result?.source;
  return (
    <article
      className={`event-card ${decision ? (accepted ? "accepted" : "rejected") : ""}`}
      data-testid="event-card"
    >
      <div className="event-icon">
        {["verification_failed", "error", "completion_rejected"].includes(
          event.kind,
        ) ? (
          <AlertTriangle size={16} />
        ) : decision ? (
          accepted ? (
            <ShieldCheck size={16} />
          ) : (
            <AlertTriangle size={16} />
          )
        ) : event.kind === "tool_requested" ? (
          <Terminal size={16} />
        ) : ["model_summary", "follow_up_proposed"].includes(event.kind) ? (
          <GitBranch size={16} />
        ) : (
          <Check size={15} />
        )}
      </div>
      <div className="event-content">
        <header>
          <strong>{eventNames[event.kind] || human(event.kind)}</strong>
          <span className="event-time" title="Recorded elapsed execution time">
            {event.kind === "execution_finished" && event.elapsed_seconds === 0
              ? "—"
              : `${Math.floor(event.elapsed_seconds / 60)
                  .toString()
                  .padStart(2, "0")}:${Math.floor(event.elapsed_seconds % 60)
                  .toString()
                  .padStart(2, "0")}`}
          </span>
        </header>
        {d.name && <code className="tool-name">{d.name}</code>}
        {decision && (
          <>
            <div className="decision-row">
              <Badge value={accepted ? "accepted" : "rejected"} />
              <span>{d.result?.reason}</span>
            </div>
            <p>
              {d.result?.proposal?.claim}:{" "}
              <code>{d.result?.proposal?.value}</code>
            </p>
            {d.result?.proposal?.quote && (
              <blockquote>{d.result.proposal.quote}</blockquote>
            )}
          </>
        )}
        {event.kind === "model_summary" && (
          <>
            <span className="eyebrow amber-text">
              MODEL CONTENT · NOT THE AUDIT AUTHORITY
            </span>
            <p>{d.summary}</p>
          </>
        )}
        {event.kind === "follow_up_proposed" && (
          <>
            <span className="eyebrow amber-text">
              EXPERIMENTAL · UNVERIFIED MODEL QUESTION · NO ACTION AUTHORIZED
            </span>
            <p>{d.proposal?.question}</p>
            <p>
              {d.linked ? "Scope and citation links checked" : "Links rejected"}
              : {d.reason}
            </p>
            {Array.isArray(d.sources) &&
              d.sources.map((s: string) => (
                <button
                  className="source-link"
                  key={s}
                  onClick={() => onSource(s)}
                >
                  Inspect cited source
                </button>
              ))}
          </>
        )}
        {d.message && <p>{d.message}</p>}
        {event.kind === "verification_failed" && Array.isArray(d.errors) && (
          <ul>
            {d.errors.map((error: string, i: number) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        )}
        {source && (
          <button className="source-link" onClick={() => onSource(source)}>
            <FileJson size={13} />
            Inspect supporting source
          </button>
        )}
        <button
          className="event-expand"
          onClick={() => setExpanded(!expanded)}
          aria-expanded={expanded}
        >
          {expanded ? "Hide" : "Show"} event details
        </button>
        {expanded && (
          <pre className="event-json">{JSON.stringify(d, null, 2)}</pre>
        )}
      </div>
    </article>
  );
}
export function ResultPanel({
  run,
  onEvidence,
}: {
  run: Run | null;
  onEvidence: (id: string) => void;
}) {
  const report = run?.status === "verification_failed" ? null : run?.report;
  return (
    <aside className="results-column">
      <div className="section-heading">
        <ShieldCheck size={16} />
        <h2>Validated results</h2>
      </div>
      {!report ? (
        <div className="panel result-placeholder">
          <ShieldCheck size={32} />
          <h3>
            {run &&
            [
              "failed",
              "cancelled",
              "interrupted",
              "verification_failed",
            ].includes(run.status)
              ? "No assessment published"
              : "Evidence before certainty."}
          </h3>
          <p>
            {run &&
            [
              "failed",
              "cancelled",
              "interrupted",
              "verification_failed",
            ].includes(run.status)
              ? run.status === "verification_failed"
                ? "Independent evidence verification failed. Review the recorded validation errors; no audit conclusion was published."
                : "This execution did not complete. Review its events and retry when ready. No successful conclusion was issued."
              : "The independent validator will publish its assessment here. Model proposals never set the conclusion."}
          </p>
        </div>
      ) : (
        <>
          <section className="panel conclusion">
            <span className="eyebrow">DETERMINISTIC ASSESSMENT</span>
            <div>
              <Badge value={report.conclusion} />
            </div>
            <p>
              {report.conclusion === "VERIFIED_WITHIN_SCOPE"
                ? "Required states are proven within this investigation’s declared scope."
                : report.conclusion === "NON_COMPLIANT"
                  ? "The admitted evidence establishes a policy violation."
                  : report.conclusion === "NOT_APPLICABLE"
                    ? "The request does not authorize deletion."
                    : "The available evidence does not establish every required state."}
            </p>
            {run?.status !== "completed" && (
              <p className="amber-text">
                Execution is {human(run?.status || "unknown")}. This is not a
                completed agent investigation.
              </p>
            )}
          </section>
          <section className="panel">
            <div className="panel-heading">
              <h3>Policy obligations</h3>
              <span className="count">{report.assessments.length}</span>
            </div>
            {report.assessments.map((a) => (
              <div className="obligation" key={a.system + a.resource}>
                <div>
                  <code>{a.resource}</code>
                  <Badge value={a.status} />
                </div>
                <span className="muted">{a.system}</span>
                <p>{a.reason}</p>
                {a.evidence.map((id) => (
                  <button
                    key={id}
                    className="source-link"
                    onClick={() => onEvidence(id)}
                  >
                    <FileJson size={13} />
                    {id}
                  </button>
                ))}
              </div>
            ))}
          </section>
          {report.unresolved.length > 0 && (
            <section className="panel">
              <h3>Unresolved questions</h3>
              <ul className="question-list">
                {report.unresolved.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </section>
          )}
          <section className="panel">
            <h3>Recommended actions</h3>
            {report.recommendations.length ? (
              report.recommendations.map((a, i) => (
                <div className="recommendation" key={i}>
                  <span className="step-number">{i + 1}</span>
                  <div>
                    <strong>{human(String(a.action))}</strong>
                    <code>
                      {String(a.system)} / {String(a.resource)}
                    </code>
                    <p>
                      {{
                        DELETE: "Verify record absent",
                        RETAIN: "Verify record retained",
                        REDACT: "Verify required fields redacted",
                        ANONYMIZE: "Verify irreversible unlinking",
                        DISABLE: "Verify flow disabled",
                        BLOCK: "Verify restore blocked",
                      }[String(a.action)] || "Verify required final state"}{" "}
                      · proposed only, execution not authorized
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="muted">
                No remediation action is currently established.
              </p>
            )}
          </section>
          <a
            className="button secondary full"
            href={`${base}/runs/${run?.id}/report`}
          >
            Export investigation report <ArrowUpRight size={15} />
          </a>
        </>
      )}
    </aside>
  );
}
