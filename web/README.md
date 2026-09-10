# TraceRAG web alpha

The hosted product is a Next.js App Router application backed by Supabase.

## Product loop

1. Sign up.
2. Create a workspace and project.
3. Register an existing HTTPS RAG endpoint.
4. Configure the JSON paths for the question, answer and optional sources.
5. Create an eval dataset.
6. Run the release gate from the dashboard or CI.
7. Promote a passing run to the project baseline.

The endpoint runner rejects localhost/private networks, does not follow redirects and caps JSON responses at 1 MiB.

## Environment

Copy `.env.example` to `.env.local`.

`TRACERAG_ENCRYPTION_KEY` must be a cryptographically random 32-byte value encoded as base64. It is server-only.

Never expose `SUPABASE_SECRET_KEY` or `TRACERAG_ENCRYPTION_KEY` through a `NEXT_PUBLIC_` variable.

## Database

Apply `../supabase/schema.sql` to a dedicated Supabase project, then run the Supabase security advisors before connecting real data.

## CI API

`POST /api/v1/projects/:projectId/runs` authenticates with a TraceRAG API key.

A passing gate returns HTTP 200. A regression returns HTTP 409 so `curl --fail-with-body` can stop a pipeline.

## Alpha constraints

- synchronous runs only;
- maximum 25 cases per run;
- POST + JSON RAG endpoints only;
- deterministic phrase/source checks, not LLM-as-judge;
- no billing yet;
- no background queue yet;
- no self-hosted runner yet.
