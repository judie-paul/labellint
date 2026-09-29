import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowDownToLine,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  FlaskConical,
  LoaderCircle,
  Search,
  Table2,
  Trash2,
  Upload,
  Users,
  X,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./style.css";

type Annotation = {
  record_id: string;
  item_id: string;
  prompt: string;
  response: string;
  rationale: string;
  annotator_id: string;
  rating: number;
  time_spent_sec: number;
  aspect: string;
  source: string;
};
type Finding = { detector: string; score: number; reason: string };
type Row = {
  record: Annotation;
  risk: number;
  flagged: boolean;
  findings: Finding[];
  note: string | null;
};
type Worker = {
  annotator_id: string;
  records: number;
  flagged: number;
  risk: number;
};
type Metrics = {
  precision: number;
  recall: number;
  f1: number;
  false_positive_rate: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
};
type Result = {
  scan: { records: Row[]; annotators: Worker[]; alpha: number | null };
  evaluation: {
    overall: Metrics;
    per_detector: Record<string, Metrics>;
  } | null;
};
type Job = {
  id: string;
  name: string;
  status: string;
  records: number;
  error?: string;
};
type View = "records" | "annotators" | "evaluation";
const percent = (n: number) => `${(n * 100).toFixed(1)}%`;

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new Error(
      typeof error.detail === "string" ? error.detail : "Invalid request",
    );
  }
  return response.json();
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [job, setJob] = useState<Job | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [view, setView] = useState<View>("records");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [detector, setDetector] = useState("all");
  const [flagged, setFlagged] = useState(true);
  const [selected, setSelected] = useState<Row | null>(null);
  const [page, setPage] = useState(0);
  const [seed, setSeed] = useState(42);
  const upload = useRef<HTMLInputElement>(null);

  async function refresh() {
    const next = await request<Job[]>("/api/jobs");
    setJobs(next);
    return next;
  }
  function choose(next: Job) {
    setJob(next);
    setResult(null);
    setSelected(null);
    setPage(0);
    setQuery("");
  }
  useEffect(() => {
    refresh()
      .then((next) => {
        if (next[0]) choose(next[0]);
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (!job) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const status = await request<Job>(`/api/jobs/${job.id}`);
        if (cancelled) return;
        if (status.status === "completed") {
          const data = await request<Result>(`/api/jobs/${job.id}/results`);
          if (!cancelled) {
            setResult(data);
            setJob(status);
            setBusy(false);
            await refresh();
          }
        } else if (status.status === "failed") {
          setError(status.error || "Audit failed");
          setBusy(false);
          setJob(status);
        } else {
          setBusy(true);
          timer = setTimeout(poll, 700);
        }
      } catch (e) {
        if (!cancelled) {
          setError((e as Error).message);
          setBusy(false);
        }
      }
    };
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [job?.id]);
  useEffect(() => {
    setPage(0);
  }, [query, detector, flagged]);
  useEffect(() => {
    const close = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelected(null);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);

  async function start(file?: File) {
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      if (file) body.append("file", file);
      const next = await request<Job>(
        file ? "/api/jobs" : "/api/demo",
        file
          ? { method: "POST", body }
          : {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ seed, items: 100 }),
            },
      );
      choose(next);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
      setBusy(false);
    }
  }
  async function remove() {
    if (!job || !window.confirm("Delete this audit from the current session?"))
      return;
    const response = await fetch(`/api/jobs/${job.id}`, { method: "DELETE" });
    if (!response.ok) {
      setError("Could not delete audit");
      return;
    }
    setJob(null);
    setResult(null);
    setSelected(null);
    try {
      const next = await refresh();
      if (next[0]) choose(next[0]);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  function download() {
    if (!result) return;
    const link = document.createElement("a");
    link.href = URL.createObjectURL(
      new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }),
    );
    link.download = "labellint-audit.json";
    link.click();
    URL.revokeObjectURL(link.href);
  }
  const rows = result?.scan.records || [];
  const filtered = rows.filter(
    (row) =>
      (!flagged || row.flagged) &&
      (detector === "all" ||
        row.findings.some((f) => f.detector === detector)) &&
      `${row.record.record_id} ${row.record.annotator_id} ${row.record.prompt} ${row.record.rationale}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const displayed = filtered.slice(page * 25, (page + 1) * 25);
  const counts = ["duplicate", "contradiction", "speed", "agreement"].map(
    (name) => ({
      name,
      records: rows.filter((r) => r.findings.some((f) => f.detector === name))
        .length,
    }),
  );
  const evalRows = Object.entries(result?.evaluation?.per_detector || {}).map(
    ([name, m]) => ({
      name,
      Precision: m.precision,
      Recall: m.recall,
      F1: m.f1,
    }),
  );

  return (
    <div className="workspace">
      <aside className="sidebar">
        <div className="brand">
          <ClipboardCheck size={28} strokeWidth={2.2} />
          <span>LabelLint</span>
        </div>
        <div className="workspace-label">ANNOTATION QUALITY</div>
        <nav aria-label="Main navigation">
          {(
            [
              ["records", Table2, "Record review"],
              ["annotators", Users, "Annotators"],
              ["evaluation", Activity, "Evaluation"],
            ] as const
          ).map(([key, Icon, label]) => (
            <button
              key={key}
              className={view === key ? "nav active" : "nav"}
              onClick={() => {
                setView(key);
                setSelected(null);
              }}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="status-dot" /> Local workspace
          <span className="version">v1.0</span>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            Audits <span className="slash">/</span>{" "}
            {job ? job.name : "New audit"}
          </span>
          <span className="local-badge">
            {busy
              ? "Processing"
              : job?.status === "completed"
                ? "Complete"
                : "Ready"}
          </span>
        </header>
        <section className="page-heading">
          <div>
            <div className="eyebrow">QUALITY CONTROL</div>
            <h1>
              {view === "records"
                ? "Record review"
                : view === "annotators"
                  ? "Annotators"
                  : "Evaluation"}
            </h1>
          </div>
          <div className="actions">
            <button
              className="icon-button"
              title="Download audit JSON"
              aria-label="Download audit JSON"
              onClick={download}
              disabled={!result}
            >
              <ArrowDownToLine size={19} />
            </button>
            <button
              className="icon-button"
              title="Delete audit"
              aria-label="Delete audit"
              onClick={remove}
              disabled={!job || busy}
            >
              <Trash2 size={18} />
            </button>
            <button
              className="primary"
              onClick={() => upload.current?.click()}
              disabled={busy}
            >
              <Upload size={17} />
              Upload data
            </button>
            <input
              ref={upload}
              type="file"
              accept=".csv,.jsonl"
              hidden
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) start(file);
                e.target.value = "";
              }}
            />
          </div>
        </section>
        <div className="dataset-bar">
          <label>
            Audit{" "}
            <select
              aria-label="Audit"
              value={job?.id || ""}
              onChange={(e) => {
                const next = jobs.find((j) => j.id === e.target.value);
                if (next) choose(next);
              }}
              disabled={busy}
            >
              <option value="" disabled>
                Select an audit
              </option>
              {jobs.map((j) => (
                <option value={j.id} key={j.id}>
                  {j.name} · {j.records} records
                </option>
              ))}
            </select>
          </label>
          <div className="sample-controls">
            <label>
              Seed{" "}
              <input
                aria-label="Seed"
                type="number"
                min={0}
                value={seed}
                onChange={(e) => setSeed(Math.max(0, Number(e.target.value)))}
              />
            </label>
            <button onClick={() => start()} disabled={busy}>
              <FlaskConical size={16} />
              Run sample
            </button>
          </div>
        </div>
        {error && (
          <div className="error" role="alert">
            {error}
            <button
              className="icon-button"
              aria-label="Dismiss error"
              onClick={() => setError("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
        {busy && (
          <div className="loading" role="status">
            <LoaderCircle className="spin" size={20} /> Auditing annotations…
          </div>
        )}
        {!result && !busy && (
          <div className="empty">
            <ClipboardCheck size={48} strokeWidth={1.4} />
            <h2>No audit selected</h2>
            <div className="actions">
              <button
                className="primary"
                onClick={() => upload.current?.click()}
              >
                <Upload size={17} />
                Upload data
              </button>
              <button onClick={() => start()}>
                <FlaskConical size={17} />
                Run sample
              </button>
            </div>
          </div>
        )}
        {result && (
          <>
            <section className="metrics" aria-label="Audit summary">
              {[
                ["Records audited", rows.length.toLocaleString(), "total"],
                [
                  "Flagged for review",
                  rows.filter((r) => r.flagged).length.toLocaleString(),
                  "warning",
                ],
                [
                  "Annotators",
                  result.scan.annotators.length.toString(),
                  "total",
                ],
                [
                  "Ordinal agreement",
                  result.scan.alpha?.toFixed(3) ?? "N/A",
                  "total",
                ],
              ].map(([label, value, tone]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong className={tone}>{value}</strong>
                </div>
              ))}
            </section>
            {view === "records" && (
              <>
                <div className="section-top">
                  <h2>
                    Review queue <span>{filtered.length}</span>
                  </h2>
                  <label className="checkbox">
                    <input
                      type="checkbox"
                      checked={flagged}
                      onChange={(e) => setFlagged(e.target.checked)}
                    />
                    Flagged only
                  </label>
                </div>
                <div className="filters">
                  <label className="search">
                    <Search size={17} />
                    <input
                      aria-label="Search records"
                      placeholder="Search records or annotators"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </label>
                  <select
                    aria-label="Detector filter"
                    value={detector}
                    onChange={(e) => setDetector(e.target.value)}
                  >
                    <option value="all">All detectors</option>
                    {counts.map((c) => (
                      <option key={c.name} value={c.name}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Record / prompt</th>
                        <th>Annotator</th>
                        <th>Rating</th>
                        <th>Signals</th>
                        <th>Risk</th>
                        <th aria-label="Open record" />
                      </tr>
                    </thead>
                    <tbody>
                      {displayed.map((row) => (
                        <tr key={row.record.record_id}>
                          <td>
                            <button
                              className="record-link"
                              onClick={() => setSelected(row)}
                            >
                              {row.record.record_id}
                            </button>
                            <span className="truncate">
                              {row.record.prompt}
                            </span>
                          </td>
                          <td>
                            <button
                              className="text-button"
                              onClick={() => setQuery(row.record.annotator_id)}
                            >
                              {row.record.annotator_id}
                            </button>
                          </td>
                          <td>
                            {row.record.rating}
                            <span className="muted"> / 5</span>
                          </td>
                          <td>
                            <div className="tags">
                              {row.findings.length ? (
                                row.findings.map((f) => (
                                  <span
                                    className={`tag ${f.detector}`}
                                    key={f.detector}
                                  >
                                    {f.detector}
                                  </span>
                                ))
                              ) : (
                                <span className="clean">
                                  <CheckCheck size={14} />
                                  Clear
                                </span>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="risk">
                              <span>{percent(row.risk)}</span>
                              <div>
                                <i style={{ width: percent(row.risk) }} />
                              </div>
                            </div>
                          </td>
                          <td>
                            <button
                              className="icon-button"
                              aria-label={`Review ${row.record.record_id}`}
                              onClick={() => setSelected(row)}
                            >
                              <ChevronRight size={17} />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {!displayed.length && (
                    <div className="empty-small">No matching records</div>
                  )}
                </div>
                <footer className="pagination">
                  <span>
                    {filtered.length ? page * 25 + 1 : 0}–
                    {Math.min((page + 1) * 25, filtered.length)} of{" "}
                    {filtered.length}
                  </span>
                  <div>
                    <button
                      className="icon-button"
                      aria-label="Previous page"
                      disabled={page === 0}
                      onClick={() => setPage(page - 1)}
                    >
                      <ChevronLeft size={17} />
                    </button>
                    <button
                      className="icon-button"
                      aria-label="Next page"
                      disabled={(page + 1) * 25 >= filtered.length}
                      onClick={() => setPage(page + 1)}
                    >
                      <ChevronRight size={17} />
                    </button>
                  </div>
                </footer>
              </>
            )}
            {view === "annotators" && (
              <>
                <div className="section-top">
                  <h2>Annotator risk</h2>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Annotator</th>
                        <th>Records</th>
                        <th>Flagged</th>
                        <th>Mean risk</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {[...result.scan.annotators]
                        .sort((a, b) => b.risk - a.risk)
                        .map((w) => (
                          <tr key={w.annotator_id}>
                            <td>{w.annotator_id}</td>
                            <td>{w.records}</td>
                            <td>{w.flagged}</td>
                            <td>{percent(w.risk)}</td>
                            <td>
                              <button
                                onClick={() => {
                                  setQuery(w.annotator_id);
                                  setFlagged(false);
                                  setDetector("all");
                                  setView("records");
                                }}
                              >
                                View records
                                <ChevronRight size={15} />
                              </button>
                            </td>
                          </tr>
                        ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            {view === "evaluation" && (
              <>
                <div className="section-top">
                  <h2>Detector signals</h2>
                </div>
                <div className="chart" data-testid="signals-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={counts}>
                      <CartesianGrid vertical={false} stroke="#e8eceb" />
                      <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Bar dataKey="records" fill="#187b70" maxBarSize={70} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {result.evaluation ? (
                  <>
                    <div className="section-top">
                      <h2>Against ground truth</h2>
                      <span className="muted">Labeled records</span>
                    </div>
                    <div className="metrics compact">
                      {(
                        [
                          "precision",
                          "recall",
                          "f1",
                          "false_positive_rate",
                        ] as const
                      ).map((key) => (
                        <div key={key}>
                          <span>{key.replaceAll("_", " ")}</span>
                          <strong>
                            {percent(result.evaluation!.overall[key])}
                          </strong>
                        </div>
                      ))}
                    </div>
                    <div className="chart">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={evalRows}>
                          <CartesianGrid vertical={false} stroke="#e8eceb" />
                          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                          <YAxis domain={[0, 1]} />
                          <Tooltip />
                          <Legend />
                          <Bar dataKey="Precision" fill="#187b70" />
                          <Bar dataKey="Recall" fill="#d98c42" />
                          <Bar dataKey="F1" fill="#667888" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </>
                ) : (
                  <div className="empty-small">
                    Ground truth unavailable for this audit
                  </div>
                )}
              </>
            )}
          </>
        )}
      </main>
      {selected && (
        <div className="drawer-backdrop" onClick={() => setSelected(null)}>
          <aside
            className="drawer"
            role="dialog"
            onKeyDown={(event) => {
              if (event.key === "Tab") event.preventDefault();
            }}
            aria-modal="true"
            aria-label="Record details"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="drawer-heading">
              <h2>Record details</h2>
              <button
                autoFocus
                className="icon-button"
                aria-label="Close record"
                onClick={() => setSelected(null)}
              >
                <X size={20} />
              </button>
            </div>
            <div className="record-id">{selected.record.record_id}</div>
            <dl>
              <dt>Annotator</dt>
              <dd>{selected.record.annotator_id}</dd>
              <dt>Rating</dt>
              <dd>{selected.record.rating} / 5</dd>
              <dt>Time</dt>
              <dd>{selected.record.time_spent_sec.toFixed(1)} sec</dd>
              <dt>Aspect</dt>
              <dd>{selected.record.aspect}</dd>
            </dl>
            {(["prompt", "response", "rationale"] as const).map((key) => (
              <section key={key}>
                <h3>{key}</h3>
                <p>{selected.record[key]}</p>
              </section>
            ))}
            <section>
              <h3>Evidence</h3>
              {selected.findings.map((f) => (
                <div className="evidence" key={f.detector}>
                  <span className={`tag ${f.detector}`}>{f.detector}</span>
                  <p>{f.reason}</p>
                </div>
              ))}
              {!selected.findings.length && <p>No flags</p>}
            </section>
            {selected.note && (
              <section>
                <h3>Reviewer note</h3>
                <p>{selected.note}</p>
              </section>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
