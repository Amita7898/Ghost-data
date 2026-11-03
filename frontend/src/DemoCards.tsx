import { ArrowUpRight, Loader2, Play } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type Demo, type Run } from "./api";
import { ErrorBox } from "./components";

export default function DemoCards({ compact = false }: { compact?: boolean }) {
  const [demos, setDemos] = useState<Demo[]>([]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();
  useEffect(() => {
    api<Demo[]>("/demos")
      .then(setDemos)
      .catch((e) => setError(e.message));
  }, []);
  async function open(id: string) {
    setBusy(id);
    setError("");
    try {
      const run = await api<Run>(`/demos/${id}/open`, { method: "POST" });
      navigate(
        `/investigations/${run.investigation_id}?run=${run.id}&replay=1`,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <section className={`demo-section ${compact ? "compact" : ""}`}>
      <div className="section-heading">
        <div>
          <span className="eyebrow">NO MODEL REQUIRED</span>
          <h2>Explore a real recorded investigation</h2>
        </div>
        <span className="badge amber">Offline replay</span>
      </div>
      {error && <ErrorBox message={error} />}
      <div className="demo-grid">
        {demos.map((d) => (
          <button
            className="demo-card"
            onClick={() => open(d.id)}
            disabled={!!busy}
            key={d.id}
          >
            <div className="demo-icon">
              {busy === d.id ? (
                <Loader2 className="spin" size={22} />
              ) : (
                <Play size={21} />
              )}
            </div>
            <div>
              <h3>{d.title}</h3>
              <p>{d.description}</p>
              <small>
                {d.turns} real model turns <span>·</span> {d.events} recorded
                events
              </small>
            </div>
            <ArrowUpRight size={18} />
          </button>
        ))}
      </div>
    </section>
  );
}
