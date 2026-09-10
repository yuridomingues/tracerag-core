import { ApiKeyCreator } from "@/components/api-key-creator";
import { requireProject } from "@/lib/auth";
import {
  createCaseAction,
  createDatasetAction,
  createEndpointAction,
  runDatasetAction,
} from "../../actions";

function pct(value: number | null) {
  return value === null ? "—" : `${(Number(value) * 100).toFixed(1)}%`;
}

export default async function ProjectPage({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<{ error?: string; run?: string }>;
}) {
  const { projectId } = await params;
  const query = await searchParams;
  const { supabase, project } = await requireProject(projectId);

  const [{ data: endpoints }, { data: datasets }, { data: cases }, { data: runs }] =
    await Promise.all([
      supabase.from("rag_endpoints")
        .select("id, name, url, question_path, response_text_path, response_sources_path, created_at")
        .eq("project_id", projectId).order("created_at"),
      supabase.from("datasets").select("id, name, created_at")
        .eq("project_id", projectId).order("created_at"),
      supabase.from("eval_cases").select("id, dataset_id, question, expected_sources, created_at")
        .order("created_at"),
      supabase.from("eval_runs")
        .select("id, status, total_cases, success_rate, keyword_pass_rate, source_recall, p95_latency_ms, gate_passed, gate_reasons, branch, git_sha, created_at")
        .eq("project_id", projectId).order("created_at", { ascending: false }).limit(20),
    ]);

  const projectCases = (cases ?? []).filter((testCase) =>
    (datasets ?? []).some((dataset) => dataset.id === testCase.dataset_id),
  );

  return (
    <main className="container stack">
      <section className="dashboard-header">
        <p className="eyebrow">Project</p>
        <h2>{project.name}</h2>
        <p className="muted code small">project_id: {project.id}</p>
        <p className="muted small">Baseline: {project.baseline_run_id ?? "not set"}</p>
      </section>

      {query.error ? <div className="notice error">{query.error}</div> : null}
      {query.run ? <div className="notice">Run <span className="code">{query.run}</span> finished. See it below.</div> : null}

      <section className="grid grid-2">
        <article className="card stack">
          <div><p className="eyebrow">Target</p><h3>Add RAG endpoint</h3><p className="muted small">HTTPS only. Private/local network targets are rejected.</p></div>
          <form className="form" action={createEndpointAction}>
            <input type="hidden" name="project_id" value={projectId} />
            <input name="name" placeholder="Production API" required />
            <input name="url" type="url" placeholder="https://api.example.com/ask" required />
            <div className="grid grid-2">
              <div><label>Question JSON path</label><input name="question_path" defaultValue="question" required /></div>
              <div><label>Answer JSON path</label><input name="response_text_path" defaultValue="answer" required /></div>
            </div>
            <div><label>Sources JSON path</label><input name="response_sources_path" defaultValue="sources" /></div>
            <div className="grid grid-2">
              <div><label>Auth header</label><input name="auth_header_name" placeholder="Authorization" /></div>
              <div><label>Auth header value</label><input name="auth_secret" type="password" placeholder="Bearer …" autoComplete="off" /></div>
            </div>
            <button className="button primary" type="submit">Save endpoint</button>
          </form>
        </article>

        <article className="card stack">
          <div><p className="eyebrow">Dataset</p><h3>Create eval dataset</h3></div>
          <form className="form" action={createDatasetAction}>
            <input type="hidden" name="project_id" value={projectId} />
            <input name="name" placeholder="Release contract v1" required />
            <button className="button primary" type="submit">Create dataset</button>
          </form>
          <div style={{ borderTop: "1px solid var(--border)", paddingTop: 18 }}>
            <h3>Add case</h3>
            {datasets?.length ? (
              <form className="form" action={createCaseAction}>
                <input type="hidden" name="project_id" value={projectId} />
                <select name="dataset_id" required defaultValue="">
                  <option value="" disabled>Choose dataset</option>
                  {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}
                </select>
                <textarea name="question" placeholder="What is the refund policy?" required />
                <textarea name="must_include" placeholder={"Required phrases, one per line\n30 days"} />
                <textarea name="must_not_include" placeholder={"Forbidden phrases, one per line\n90 days"} />
                <textarea name="expected_sources" placeholder={"Expected sources, one per line\nrefund-policy.pdf"} />
                <button className="button" type="submit">Add eval case</button>
              </form>
            ) : <p className="muted">Create a dataset first.</p>}
          </div>
        </article>
      </section>

      <section className="grid grid-2">
        <article className="card stack">
          <div><p className="eyebrow">Run</p><h3>Execute release gate</h3></div>
          {endpoints?.length && datasets?.length ? (
            <form className="form" action={runDatasetAction}>
              <input type="hidden" name="project_id" value={projectId} />
              <select name="endpoint_id" required defaultValue="">
                <option value="" disabled>Endpoint</option>
                {endpoints.map((endpoint) => <option key={endpoint.id} value={endpoint.id}>{endpoint.name}</option>)}
              </select>
              <select name="dataset_id" required defaultValue="">
                <option value="" disabled>Dataset</option>
                {datasets.map((dataset) => <option key={dataset.id} value={dataset.id}>{dataset.name}</option>)}
              </select>
              <label className="row"><input style={{ width: "auto" }} type="checkbox" name="set_as_baseline" />Set as baseline if the gate passes</label>
              <button className="button primary" type="submit">Run evaluation</button>
            </form>
          ) : <p className="muted">Add at least one endpoint and dataset first.</p>}
          <p className="muted small">Alpha limit: 20 cases per synchronous run.</p>
        </article>
        <article className="card"><p className="eyebrow">CI</p><h3>Create API key</h3><ApiKeyCreator projectId={projectId} /></article>
      </section>

      <section className="card">
        <p className="eyebrow">Inventory</p>
        <div className="grid grid-3">
          <div><div className="metric">{endpoints?.length ?? 0}</div><div className="muted small">endpoints</div></div>
          <div><div className="metric">{datasets?.length ?? 0}</div><div className="muted small">datasets</div></div>
          <div><div className="metric">{projectCases.length}</div><div className="muted small">eval cases</div></div>
        </div>
      </section>

      <section className="card">
        <p className="eyebrow">Run history</p><h3>Latest evaluations</h3>
        {runs?.length ? (
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead><tr><th>Run</th><th>Gate</th><th>Success</th><th>Keywords</th><th>Sources</th><th>P95</th><th>Git</th></tr></thead>
              <tbody>{runs.map((run) => (
                <tr key={run.id}>
                  <td className="code small">{run.id.slice(0, 8)}</td>
                  <td className={run.status !== "completed" ? "status-running" : run.gate_passed ? "status-pass" : "status-fail"} title={(run.gate_reasons ?? []).join("\n")}>
                    {run.status !== "completed" ? run.status : run.gate_passed ? "PASS" : "FAIL"}
                  </td>
                  <td>{pct(run.success_rate)}</td><td>{pct(run.keyword_pass_rate)}</td><td>{pct(run.source_recall)}</td>
                  <td>{run.p95_latency_ms === null ? "—" : `${Math.round(Number(run.p95_latency_ms))} ms`}</td>
                  <td className="small code">{run.branch ?? "—"} {run.git_sha ? run.git_sha.slice(0, 7) : ""}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : <p className="muted">No runs yet.</p>}
      </section>

      <section className="card">
        <p className="eyebrow">CI contract</p><h3>Call the release gate from any pipeline</h3>
        <pre>{`curl --fail-with-body -X POST \\\n  "$TRACERAG_URL/api/v1/projects/${projectId}/runs" \\\n  -H "Authorization: Bearer $TRACERAG_API_KEY" \\\n  -H "Content-Type: application/json" \\\n  -d '{"dataset_id":"DATASET_ID","endpoint_id":"ENDPOINT_ID","git_sha":"'$GITHUB_SHA'","branch":"'$GITHUB_REF_NAME'"}'`}</pre>
        <p className="muted small">HTTP 200 means pass. HTTP 409 means regression.</p>
      </section>
    </main>
  );
}
