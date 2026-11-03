import { ArrowLeft, Database, Loader2, Plus, UploadCloud } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, human, upload, type Bundle, type Investigation } from "../api";
import { ErrorBox } from "../components";
import DemoCards from "../DemoCards";

export default function NewInvestigation() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [subject, setSubject] = useState("");
  const [cutoff, setCutoff] = useState("");
  const [cutoffEdited, setCutoffEdited] = useState(false);
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [scope, setScope] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [example, setExample] = useState("");
  async function chooseFile(f: File) {
    try {
      if (f.size > 5_000_000) throw new Error("Maximum evidence size is 5 MB.");
      if (!f.name.toLowerCase().endsWith(".json"))
        throw new Error("Only structured JSON bundles are supported.");
      const b = JSON.parse(await f.text()) as Bundle;
      if (!b.request || !Array.isArray(b.targets))
        throw new Error("Choose a Ghost Data structured evidence bundle.");
      setBundle(b);
      setFile(f);
      setCutoff(new Date(b.request.audit_at).toISOString().slice(0, 19));
      setCutoffEdited(false);
      setSubject(b.request.identifier.value);
      setScope(b.targets.map((t) => JSON.stringify([t.system, t.resource])));
      if (!title)
        setTitle(
          "Deletion audit · " + b.request.identifier.value.split("@")[0],
        );
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function chooseExample(key: string) {
    setExample(key);
    if (!key) return;
    try {
      const b = await api<Bundle>("/examples/" + key);
      await chooseFile(
        new File([JSON.stringify(b, null, 2)], `${key}-evidence.json`, {
          type: "application/json",
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      setError("Select a synthetic example or upload a JSON bundle.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const inv = await api<Investigation>("/investigations", {
        method: "POST",
        body: JSON.stringify({
          title,
          subject_label: subject,
          audit_at:
            cutoffEdited && cutoff
              ? cutoff.length === 16
                ? cutoff + ":00Z"
                : cutoff + "Z"
              : null,
          scope: bundle?.targets.length ? scope : null,
        }),
      });
      await upload(inv.id, file, setProgress);
      navigate("/investigations/" + inv.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="page narrow">
      <Link className="back-link" to="/">
        <ArrowLeft size={15} />
        Overview
      </Link>
      <div className="page-heading">
        <div>
          <span className="eyebrow">NEW INVESTIGATION</span>
          <h1>Start with the evidence.</h1>
          <p>Define a bounded audit. Your original evidence stays preserved.</p>
        </div>
      </div>
      <form onSubmit={submit}>
        <section className="panel form-panel">
          <div className="panel-heading">
            <h2>
              <span className="step-number">01</span> Evidence bundle
            </h2>
            <span className="badge neutral">JSON only · 5 MB max</span>
          </div>
          <label className="field">
            Use a synthetic example
            <select
              aria-label="Synthetic example"
              value={example}
              onChange={(e) => chooseExample(e.target.value)}
            >
              <option value="">Choose a ready-to-use case</option>
              <option value="receipt">Prose readback receipt</option>
              <option value="replica">Remaining replica</option>
              <option value="partial">Partial snapshot</option>
              <option value="claim">Deletion-success claim</option>
            </select>
          </label>
          <label className="upload-drop">
            <UploadCloud size={28} />
            <strong>
              {file ? file.name : "Choose a structured evidence bundle"}
            </strong>
            <span>
              {file
                ? `${(file.size / 1024).toFixed(1)} KB · ready for server validation`
                : "Identities, policies, scope and observations in one JSON file."}
            </span>
            <input
              aria-label="Upload evidence JSON"
              type="file"
              accept=".json,application/json"
              onChange={(e) => {
                if (e.target.files?.[0]) chooseFile(e.target.files[0]);
              }}
            />
          </label>
          <p className="fine-print">
            PDFs, images and raw SQL are not supported by this version. Evidence
            is validated again by the backend.
          </p>
        </section>
        <section className="panel form-panel">
          <div className="panel-heading">
            <h2>
              <span className="step-number">02</span> Investigation context
            </h2>
          </div>
          <label className="field">
            Investigation title
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={100}
              placeholder="e.g. Account deletion review"
            />
          </label>
          <div className="form-grid">
            <label className="field">
              Subject label
              <input
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                maxLength={160}
                placeholder="Display label only"
              />
              <small>
                Identity is independently resolved from the evidence.
              </small>
            </label>
            <label className="field">
              Audit cutoff · UTC
              <input
                type="datetime-local"
                step="1"
                value={cutoff}
                onChange={(e) => {
                  setCutoff(e.target.value);
                  setCutoffEdited(true);
                }}
              />
              <small>
                The exact source cutoff is preserved until you edit this UTC
                value.
              </small>
            </label>
          </div>
          <label className="field">
            Policy
            <select aria-label="Policy">
              <option>Policy embedded in evidence bundle</option>
            </select>
            <small>
              Uploaded rules remain the policy authority; the agent cannot
              change them.
            </small>
          </label>
        </section>
        {bundle && (
          <section className="panel form-panel">
            <div className="panel-heading">
              <h2>
                <span className="step-number">03</span> Resource scope
              </h2>
              <span className="count">{scope.length} selected</span>
            </div>
            <div className="scope-list">
              {bundle.targets.map((t) => {
                const key = JSON.stringify([t.system, t.resource]);
                return (
                  <label key={key}>
                    <input
                      type="checkbox"
                      checked={scope.includes(key)}
                      onChange={(e) =>
                        setScope((old) =>
                          e.target.checked
                            ? [...old, key]
                            : old.filter((k) => k !== key),
                        )
                      }
                    />
                    <Database size={16} />
                    <span>
                      <strong>{t.resource}</strong>
                      <small>
                        {t.system} · {human(t.category)}
                      </small>
                    </span>
                  </label>
                );
              })}
            </div>
            <p className="fine-print">
              Conclusions cover only the selected, declared scope. A configured
              copy is stored when you change the cutoff or scope.
            </p>
          </section>
        )}
        {error && <ErrorBox message={error} />}
        <div className="form-actions">
          <span className="muted">
            {busy
              ? `Uploading and validating… ${progress}%`
              : "Live inference starts only when you choose Start live in the workspace."}
          </span>
          <button className="button primary" disabled={busy || !file || !title}>
            {busy ? <Loader2 className="spin" size={17} /> : <Plus size={17} />}
            Create investigation
          </button>
        </div>
      </form>
      <DemoCards compact />
    </div>
  );
}
