# SaaS readiness

TraceRAG is now structured as an alpha SaaS rather than only a local RAG core.

## Implemented

- Supabase email/password authentication;
- workspace tenancy and membership model;
- RLS on every public product table;
- projects and accepted baseline runs;
- configurable HTTPS RAG endpoints;
- encrypted endpoint credentials;
- deterministic eval datasets;
- run/result persistence;
- success, keyword, source-recall and P95 metrics;
- absolute and baseline regression gates;
- hashed per-project API keys;
- CI endpoint that returns HTTP 409 on regression;
- SSRF controls for server-side endpoint execution;
- run history in the web dashboard.

## Deliberate alpha limits

The hosted runner is synchronous and capped at 25 cases. Not yet implemented:

- subscription billing;
- background queues/workers;
- GitHub App installation and Checks API annotations;
- team invitation UI;
- self-hosted runners for private-network targets;
- secret rotation;
- detailed audit logs;
- LLM-as-judge evaluations;
- broad prompt/trace observability.

## Production checklist

1. Provision a dedicated Supabase project.
2. Apply `supabase/schema.sql`.
3. Run Supabase security and performance advisors.
4. Configure Auth redirect URLs for the final domain.
5. Set a server-only 32-byte base64 `TRACERAG_ENCRYPTION_KEY`.
6. Deploy `web/` with publishable Supabase credentials plus the server secret key.
7. Verify signup, RLS isolation, API-key creation, encrypted endpoint storage and passing/failing runs.
8. Add monitoring for failed runs and server errors.
9. Publish privacy/terms before storing customer evaluation content.

## Product validation gate

Do not add broad observability features merely because competitors have them. The alpha should first prove that teams will use a black-box RAG release gate without replacing their current tracing stack.
