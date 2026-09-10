import Link from "next/link";
import { signInAction, signUpAction } from "./actions";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; message?: string }>;
}) {
  const params = await searchParams;
  return (
    <main className="auth-shell">
      <section className="card auth-card stack">
        <div>
          <Link className="brand" href="/">Trace<span>RAG</span></Link>
          <h2 style={{ marginTop: 22 }}>Sign in to your workspace</h2>
          <p className="muted">Email/password authentication is backed by Supabase.</p>
        </div>
        {params.error ? <div className="notice error">{params.error}</div> : null}
        {params.message ? <div className="notice">{params.message}</div> : null}
        <form className="form">
          <div><label htmlFor="email">Email</label><input id="email" name="email" type="email" autoComplete="email" required /></div>
          <div><label htmlFor="password">Password</label><input id="password" name="password" type="password" minLength={8} autoComplete="current-password" required /></div>
          <div className="actions">
            <button className="button primary" formAction={signInAction}>Sign in</button>
            <button className="button" formAction={signUpAction}>Create account</button>
          </div>
        </form>
      </section>
    </main>
  );
}
