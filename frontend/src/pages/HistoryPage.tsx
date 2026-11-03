import { ArrowUpRight, Download } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, base, date, human, type Run } from "../api";
import { Badge, Empty, ErrorBox } from "../components";

export default function HistoryPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  useEffect(() => {
    api<Run[]>("/runs")
      .then(setRuns)
      .catch((e) => setError(e.message));
  }, []);
  const comparison = runs.filter((r) => selected.includes(r.id));
  return (
    <div className="page">
      <div className="page-heading">
        <div>
          <span className="eyebrow">INVESTIGATION HISTORY</span>
          <h1>Every run leaves a record.</h1>
          <p>
            Review recorded activity, execution outcomes, and evidence-backed
            reports.
          </p>
        </div>
        <span className="badge neutral">{runs.length} saved runs</span>
      </div>
      {error && <ErrorBox message={error} />}
      <section className="panel">
        <div className="panel-heading">
          <h2>Run ledger</h2>
          <span className="muted">Select two runs to compare summaries</span>
        </div>
        {runs.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th />
                  <th>Run</th>
                  <th>Mode</th>
                  <th>Execution</th>
                  <th>Conclusion</th>
                  <th>Created</th>
                  <th>Report</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <input
                        aria-label={`Compare run ${r.id}`}
                        type="checkbox"
                        checked={selected.includes(r.id)}
                        disabled={
                          selected.length >= 2 && !selected.includes(r.id)
                        }
                        onChange={(e) =>
                          setSelected((old) =>
                            e.target.checked
                              ? [...old, r.id]
                              : old.filter((id) => id !== r.id),
                          )
                        }
                      />
                    </td>
                    <td>
                      <Link
                        className="text-link"
                        to={`/investigations/${r.investigation_id}?run=${r.id}`}
                      >
                        {r.id.slice(0, 8)} <ArrowUpRight size={12} />
                      </Link>
                    </td>
                    <td>
                      <Badge value={r.mode} mode />
                    </td>
                    <td>
                      <Badge value={r.status} />
                    </td>
                    <td>
                      {r.conclusion ? (
                        <Badge value={r.conclusion} />
                      ) : (
                        <span className="muted">No assessment</span>
                      )}
                    </td>
                    <td className="muted">{date(r.created_at)}</td>
                    <td>
                      <a
                        aria-label={`Export report ${r.id}`}
                        className="icon-button"
                        href={`${base}/runs/${r.id}/report`}
                      >
                        <Download size={16} />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty title="No saved runs">
            Open a recording or start a live investigation.
          </Empty>
        )}
      </section>
      {comparison.length === 2 && (
        <section className="panel">
          <div className="panel-heading">
            <h2>Run summary comparison</h2>
            <span className="muted">
              Scopes may differ; this is not an accuracy comparison.
            </span>
          </div>
          <div className="compare-grid">
            {comparison.map((r) => (
              <div key={r.id}>
                <code>{r.id.slice(0, 8)}</code>
                <h3>{r.conclusion ? human(r.conclusion) : "No assessment"}</h3>
                <p>
                  {human(r.status)} · {r.mode}
                </p>
                <p>
                  {r.report?.assessments.length || 0} obligations ·{" "}
                  {r.report?.unresolved.length || 0} unresolved questions
                </p>
                <ul className="question-list">
                  {r.report?.assessments.map((a) => (
                    <li key={a.system + a.resource}>
                      {a.system} / {a.resource}: {human(a.status)}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
