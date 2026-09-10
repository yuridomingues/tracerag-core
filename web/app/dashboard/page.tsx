import Link from "next/link";
import { requireUser } from "@/lib/auth";
import { createProjectAction, createWorkspaceAction } from "./actions";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  const params = await searchParams;
  const { supabase } = await requireUser();
  const [{ data: workspaces }, { data: projects }] = await Promise.all([
    supabase.from("workspaces").select("id, name, slug, created_at").order("created_at"),
    supabase.from("projects").select("id, name, slug, workspace_id, created_at").order("created_at", { ascending: false }),
  ]);

  return (
    <main className="container stack">
      <section className="dashboard-header">
        <p className="eyebrow">Workspace</p>
        <h2>Release gates for the RAG APIs you already run.</h2>
        <p className="muted">Deterministic contracts, expected sources and regression against an accepted baseline.</p>
      </section>
      {params.error ? <div className="notice error">{params.error}</div> : null}
      <section className="grid grid-2">
        <div className="card stack">
          <div><h3>Create workspace</h3><p className="muted small">Workspaces are the tenancy boundary.</p></div>
          <form className="form" action={createWorkspaceAction}>
            <input name="name" placeholder="Acme AI" minLength={2} maxLength={80} required />
            <button className="button primary" type="submit">Create workspace</button>
          </form>
        </div>
        <div className="card stack">
          <div><h3>Create project</h3><p className="muted small">Projects contain endpoints, datasets, baselines and runs.</p></div>
          {workspaces?.length ? (
            <form className="form" action={createProjectAction}>
              <select name="workspace_id" required defaultValue="">
                <option value="" disabled>Choose a workspace</option>
                {workspaces.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
              </select>
              <input name="name" placeholder="Support RAG" minLength={2} maxLength={80} required />
              <button className="button primary" type="submit">Create project</button>
            </form>
          ) : <p className="muted">Create a workspace first.</p>}
        </div>
      </section>
      <section className="section">
        <p className="eyebrow">Projects</p>
        <div className="grid grid-3">
          {projects?.length ? projects.map((p) => (
            <Link key={p.id} className="card project-link" href={`/dashboard/projects/${p.id}`}>
              <h3>{p.name}</h3><p className="muted small code">{p.slug}</p>
            </Link>
          )) : <div className="card muted">No projects yet.</div>}
        </div>
      </section>
    </main>
  );
}
