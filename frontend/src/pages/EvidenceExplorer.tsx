import {
  ArrowUpRight,
  Database,
  FileJson,
  Ghost,
  GitBranch,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  api,
  date,
  upload,
  type Artifact,
  type Context,
  type Event,
  type Investigation,
  type Run,
} from "../api";
import { Badge, Empty, ErrorBox, SourceViewer } from "../components";

export default function EvidenceExplorer() {
  const { id } = useParams();
  const [cases, setCases] = useState<Investigation[]>([]);
  const [selected, setSelected] = useState(id || "");
  const [context, setContext] = useState<Context | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [source, setSource] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [proposals, setProposals] = useState<Event[]>([]);
  async function addEvidence(file: File) {
    if (!selected) return;
    setUploading(true);
    setError("");
    try {
      await upload(selected, file, setProgress);
      const [c, a] = await Promise.all([
        api<Context>(`/investigations/${selected}/context`),
        api<Artifact[]>(`/investigations/${selected}/evidence`),
      ]);
      setContext(c);
      setArtifacts(a);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }
  useEffect(() => {
    api<Investigation[]>("/investigations")
      .then((value) => {
        setCases(value);
        if (!selected && value.length) setSelected(value[0].id);
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!selected) return;
    Promise.all([
      api<Context>(`/investigations/${selected}/context`),
      api<Artifact[]>(`/investigations/${selected}/evidence`),
    ])
      .then(([c, a]) => {
        setContext(c);
        setArtifacts(a);
      })
      .catch((e) => setError(e.message));
  }, [selected]);
  useEffect(() => {
    if (!selected) return;
    api<Run[]>(`/investigations/${selected}/runs`)
      .then(async (runs) => {
        const events = runs[0]
          ? await api<Event[]>(`/runs/${runs[0].id}/events`)
          : [];
        setProposals(
          events.filter(
            (e) =>
              e.kind === "hypothesis_validated" &&
              (e.data.result as any)?.proposal?.claim === "RELATIONSHIP",
          ),
        );
      })
      .catch((e) => setError(e.message));
  }, [selected]);
  const links = context?.relationships || [];
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">EVIDENCE EXPLORER</span>
          <h1>Follow the source.</h1>
          <p>
            Inspect original artifacts and grounded relationships, without
            changing evidence.
          </p>
        </div>
        <select
          aria-label="Choose investigation"
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
        >
          <option value="">Select investigation</option>
          {cases.map((c) => (
            <option key={c.id} value={c.id}>
              {c.title}
            </option>
          ))}
        </select>
      </div>
      {error && <ErrorBox message={error} />}
      <div className="evidence-layout">
        <section className="panel">
          <div className="panel-heading">
            <h2>Registered artifacts</h2>
            <span className="count">{artifacts.length}</span>
          </div>
          {selected && (
            <label className="add-evidence">
              {uploading ? `Uploading… ${progress}%` : "Add JSON evidence"}
              <input
                aria-label="Add evidence to investigation"
                type="file"
                accept=".json,application/json"
                disabled={uploading}
                onChange={(e) => {
                  if (e.target.files?.[0]) addEvidence(e.target.files[0]);
                  e.target.value = "";
                }}
              />
            </label>
          )}
          {artifacts.length ? (
            artifacts.map((a) => (
              <button
                key={a.id}
                className="artifact-card"
                onClick={() => setSource(a.sha256)}
              >
                <FileJson size={23} />
                <div>
                  <strong>{a.filename}</strong>
                  <small>
                    {a.source} · {(a.size / 1024).toFixed(1)} KB
                  </small>
                  <code>sha256:{a.sha256.slice(0, 20)}…</code>
                </div>
                <ArrowUpRight size={16} />
              </button>
            ))
          ) : (
            <Empty title="No evidence yet">
              Create an investigation and upload a structured JSON bundle.
            </Empty>
          )}
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Source-backed relationships</h2>
            <GitBranch size={18} />
          </div>
          {links.length ? (
            <>
              <div className="relationship-map" aria-label="Relationship graph">
                <div className="graph-subject">
                  <Ghost size={20} />
                  <strong>{context?.subject}</strong>
                  <small>Resolved subject</small>
                </div>
                <div className="graph-links">
                  {links.slice(0, 6).map((l, i) => (
                    <button
                      key={i}
                      className="graph-node"
                      onClick={() => setSource(l.source)}
                    >
                      <Database size={16} />
                      <span>{l.to}</span>
                      <small>Identifier match</small>
                    </button>
                  ))}
                </div>
              </div>
              <p className="fine-print">
                Links reflect admitted source identifiers, not a deletion
                verdict or model guess.
              </p>
            </>
          ) : (
            <Empty title="No eligible links established">
              Ambiguous ownership and unavailable evidence stay unresolved.
            </Empty>
          )}
        </section>
      </div>
      <section className="panel">
        <div className="panel-heading">
          <h2>Observation inventory</h2>
          <span className="count">
            {context?.bundle?.observations.length || 0}
          </span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>System / resource</th>
                <th>Evidence type</th>
                <th>Recorded state</th>
                <th>Audit eligibility</th>
                <th>Observed</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {context?.bundle?.observations.map((o, i) => (
                <tr key={o.id}>
                  <td>
                    <code>{o.id}</code>
                  </td>
                  <td>
                    <strong>{o.resource}</strong>
                    <small>{o.system}</small>
                  </td>
                  <td>
                    <Badge value={o.kind} />
                  </td>
                  <td>
                    <Badge value={o.state} />
                  </td>
                  <td
                    title={
                      context?.eligibility?.[o.id]?.join(" · ") ||
                      "Eligible metadata does not establish a compliant state"
                    }
                  >
                    <Badge
                      value={
                        context?.eligibility?.[o.id]
                          ? context.eligibility[o.id].length
                            ? "excluded"
                            : "eligible"
                          : "not assessed"
                      }
                    />
                  </td>
                  <td className="muted">{date(o.observed_at)}</td>
                  <td>
                    <button
                      className="text-link"
                      onClick={() =>
                        setSource(
                          `sha256:${context.artifact?.sha256}#/observations/${i}`,
                        )
                      }
                    >
                      Inspect <ArrowUpRight size={13} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>Agent relationship hypotheses</h2>
          <span className="badge amber">Proposals are not source facts</span>
        </div>
        {proposals.length ? (
          proposals.map((e) => {
            const result = e.data.result as any;
            return (
              <div className="obligation" key={e.seq}>
                <Badge value={result.accepted ? "accepted" : "rejected"} />
                <p>{result.proposal.value}</p>
                <p>{result.reason}</p>
                {result.source && (
                  <button
                    className="source-link"
                    onClick={() => setSource(result.source)}
                  >
                    Inspect citation
                  </button>
                )}
              </div>
            );
          })
        ) : (
          <p className="muted">
            No model relationship hypotheses were recorded for this case. The
            graph above contains only admitted source links.
          </p>
        )}
      </section>
      {source && (
        <SourceViewer
          source={source}
          artifacts={artifacts}
          onClose={() => setSource("")}
        />
      )}
    </div>
  );
}
