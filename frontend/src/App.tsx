import {
  FolderSearch,
  Ghost,
  History,
  LayoutDashboard,
  Plus,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Link, NavLink, Route, Routes } from "react-router-dom";
import { api, type Runtime } from "./api";
import { Empty } from "./components";
import Dashboard from "./pages/Dashboard";
import EvidenceExplorer from "./pages/EvidenceExplorer";
import HistoryPage from "./pages/HistoryPage";
import NewInvestigation from "./pages/NewInvestigation";
import Workspace from "./pages/Workspace";
export default function App() {
  const [runtime, setRuntime] = useState<Runtime | null>(null);
  const check = useCallback(
    () =>
      api<Runtime>("/runtime")
        .then(setRuntime)
        .catch(() =>
          setRuntime({
            available: false,
            model: "Local model",
            message: "Backend unavailable",
          }),
        ),
    [],
  );
  useEffect(() => {
    check();
  }, [check]);
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar">
        <Link className="brand" to="/">
          <span className="brand-mark">
            <Ghost size={25} />
          </span>
          <span>
            GHOST<span className="brand-data">DATA</span>
            <small>INVESTIGATION CONSOLE</small>
          </span>
        </Link>
        <div className="sidebar-label">WORKSPACE</div>
        <nav aria-label="Main navigation">
          <NavLink end to="/">
            <LayoutDashboard size={18} />
            <span>Overview</span>
          </NavLink>
          <NavLink to="/new">
            <Plus size={18} />
            <span>New investigation</span>
          </NavLink>
          <NavLink to="/evidence">
            <FolderSearch size={18} />
            <span>Evidence explorer</span>
          </NavLink>
          <NavLink to="/history">
            <History size={18} />
            <span>Run history</span>
          </NavLink>
        </nav>
        <div className="sidebar-bottom">
          <div className="trust-icon">
            <ShieldCheck size={18} />
            <span>
              Evidence grounded.
              <br />
              Independently validated.
            </span>
          </div>
          <small>LOCAL WORKSPACE · v0.4</small>
        </div>
      </aside>
      <div className="app-main">
        <header className="global-header">
          <span>
            <span className="header-square" />
            PRIVATE INVESTIGATION WORKSPACE
          </span>
          <button
            className={`runtime-indicator ${runtime?.available ? "ready" : ""}`}
            onClick={check}
            title={runtime?.message || "Checking local runtime"}
          >
            <span className="status-dot" />
            {runtime
              ? runtime.available
                ? "Local model ready"
                : runtime.message === "Backend unavailable"
                  ? "Backend unavailable"
                  : "Replay ready · model offline"
              : "Checking local model"}
            <RefreshCw size={12} />
          </button>
        </header>
        <main id="main" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new" element={<NewInvestigation />} />
            <Route
              path="/investigations/:id"
              element={<Workspace runtime={runtime} />}
            />
            <Route path="/evidence" element={<EvidenceExplorer />} />
            <Route
              path="/investigations/:id/evidence"
              element={<EvidenceExplorer />}
            />
            <Route path="/history" element={<HistoryPage />} />
            <Route
              path="*"
              element={
                <Empty title="Page not found">
                  <Link to="/">Return to overview</Link>
                </Empty>
              }
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}
