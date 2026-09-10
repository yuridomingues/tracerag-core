import Link from "next/link";

export default function HomePage() {
  return (
    <>
      <header className="container nav">
        <Link className="brand" href="/">Trace<span>RAG</span></Link>
        <nav className="nav-links">
          <a className="muted small" href="#how-it-works">How it works</a>
          <Link className="button" href="/login">Sign in</Link>
        </nav>
      </header>
      <main>
        <section className="container hero">
          <p className="eyebrow">Regression testing for RAG APIs</p>
          <h1>Catch retrieval failures before your users do.</h1>
          <p className="lead">
            Point TraceRAG at the API you already have. Run a stable dataset,
            compare it with your production baseline and fail CI when answer
            contracts, source recall or latency regress.
          </p>
          <div className="actions">
            <Link className="button primary" href="/login">Create a project</Link>
            <a className="button" href="#how-it-works">See the workflow</a>
          </div>
        </section>
        <section className="container section" id="how-it-works">
          <div className="grid grid-3">
            <article className="card"><p className="eyebrow">01</p><h3>Use your existing endpoint</h3><p className="muted">No SDK migration. Configure where the question, answer and source list live in JSON.</p></article>
            <article className="card"><p className="eyebrow">02</p><h3>Define an eval contract</h3><p className="muted">Store questions, required phrases, forbidden phrases and expected sources.</p></article>
            <article className="card"><p className="eyebrow">03</p><h3>Gate the release</h3><p className="muted">Compare success, source recall and P95 latency against an accepted baseline.</p></article>
          </div>
        </section>
        <section className="container section">
          <div className="card">
            <p className="eyebrow">Deliberately narrow</p>
            <h2>Not another observability platform.</h2>
            <p className="lead">TraceRAG starts as a black-box release gate for teams that already have a RAG stack.</p>
          </div>
        </section>
      </main>
      <footer className="container">TraceRAG alpha · release confidence for RAG teams.</footer>
    </>
  );
}
