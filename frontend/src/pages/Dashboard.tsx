import {
  Activity,
  ChevronRight,
  Database,
  FolderSearch,
  Loader2,
  Plus,
  Search,
  ShieldCheck,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, date, terminal, type Investigation, type Run } from "../api";
import { Badge, Empty, ErrorBox } from "../components";
import DemoCards from "../DemoCards";

export default function Dashboard() {
  const [cases, setCases] = useState<Investigation[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [error, setError] = useState("");
  const [loaded, setLoaded] = useState(false);
  const [query, setQuery] = useState("");
  useEffect(() => {
    Promise.all([api<Investigation[]>("/investigations"), api<Run[]>("/runs")])
      .then(([a, b]) => {
        setCases(a);
        setRuns(b);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoaded(true));
  }, []);
  const active = runs.filter((r) => !terminal(r)).length;
  const findings = runs
    .filter((r) => r.status === "completed")
    .reduce(
      (n, r) =>
        n +
        (r.report?.assessments.filter((a) => a.status === "VIOLATED").length ||
          0),
      0,
    );
  const visible = cases.filter((c) =>
    (c.title + c.subject_label).toLowerCase().includes(query.toLowerCase()),
  );
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">GHOST DATA / OVERVIEW</span>
          <h1>Clarity beyond the deletion claim.</h1>
          <p>
            Investigate the evidence. Understand what remains. Verify every
            conclusion.
          </p>
        </div>
        <Link className="button primary" to="/new">
          <Plus size={17} />
          New investigation
        </Link>
      </div>
      {error && <ErrorBox message={error} />}
      <div className="stats-grid">
        {[
          {
            label: "Investigations",
            value: cases.length,
            icon: FolderSearch,
            note: "In this local workspace",
          },
          {
            label: "Active runs",
            value: active,
            icon: Activity,
            note: active
              ? "Real inference in progress"
              : "No live runs in progress",
          },
          {
            label: "Policy violations",
            value: findings,
            icon: ShieldCheck,
            note: "Across completed runs",
          },
          {
            label: "Evidence artifacts",
            value: cases.reduce((n, c) => n + c.evidence_count, 0),
            icon: Database,
            note: "Registered with provenance",
          },
        ].map((s) => (
          <div className="stat-card" key={s.label}>
            <div>
              <span>{s.label}</span>
              <s.icon size={17} />
            </div>
            <strong>{s.value.toString().padStart(2, "0")}</strong>
            <small>{s.note}</small>
          </div>
        ))}
      </div>
      <DemoCards />
      <section className="panel investigations-panel">
        <div className="panel-heading">
          <div>
            <h2>Investigations</h2>
            <p className="muted">
              Your evidence, activity, and validated outcomes.
            </p>
          </div>
          <label className="search-box">
            <Search size={15} />
            <input
              aria-label="Search investigations"
              placeholder="Search investigations"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
        </div>
        {!loaded ? (
          <p className="loading">
            <Loader2 className="spin" size={16} />
            Loading investigations…
          </p>
        ) : visible.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Investigation</th>
                  <th>Execution</th>
                  <th>Conclusion</th>
                  <th>Updated</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {visible.map((c) => (
                  <tr key={c.id}>
                    <td>
                      <Link
                        className="case-link"
                        to={`/investigations/${c.id}`}
                      >
                        <span className="case-icon">
                          <FolderSearch size={18} />
                        </span>
                        <span>
                          <strong>{c.title}</strong>
                          <small>
                            {c.subject_label ||
                              "Subject resolved from evidence"}
                          </small>
                        </span>
                      </Link>
                    </td>
                    <td>
                      {c.latest_run ? (
                        <>
                          <Badge value={c.latest_run.status as string} />
                          <small className="mode-text">
                            {String(c.latest_run.mode).toUpperCase()}
                          </small>
                        </>
                      ) : (
                        <Badge value="ready" />
                      )}
                    </td>
                    <td>
                      {c.latest_run?.conclusion ? (
                        <Badge value={String(c.latest_run.conclusion)} />
                      ) : (
                        <span className="muted">Awaiting analysis</span>
                      )}
                    </td>
                    <td className="muted">
                      {date(
                        (c.latest_run?.created_at as string) || c.created_at,
                      )}
                    </td>
                    <td>
                      <Link
                        aria-label={`Open ${c.title}`}
                        className="icon-button"
                        to={`/investigations/${c.id}`}
                      >
                        <ChevronRight size={17} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            title={
              query
                ? "No matching investigations"
                : "Your next investigation starts here"
            }
          >
            Create a case with a structured JSON bundle, or open a genuine
            recording above.
          </Empty>
        )}
      </section>
      <div className="local-note">
        <ShieldCheck size={14} />
        <span>
          Local-first. Read-only tools. Model proposals never override evidence
          validation.
        </span>
      </div>
    </div>
  );
}
