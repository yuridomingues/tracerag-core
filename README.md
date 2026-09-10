# TraceRAG

Black-box regression testing for RAG APIs.

TraceRAG is being built as a narrow SaaS for teams that already have a RAG application and want a deterministic release gate without migrating their production observability stack.

The repository contains two layers:

- **Core (Python):** retrieval traceability, abstention and local retrieval evaluation.
- **Web alpha (Next.js + Supabase):** accounts, workspaces, projects, endpoint contracts, eval datasets, run history, baselines and a CI API.

## Hosted workflow

```text
existing RAG API
      ↑
      │ HTTPS / JSON
TraceRAG runner
      ↑
eval dataset ──→ deterministic checks
                     │
                     ├─ success rate
                     ├─ required/forbidden phrases
                     ├─ expected-source recall
                     └─ P95 latency
                              │
                    baseline comparison
                              │
                       PASS / FAIL
                              │
                         CI release gate
```

## Security boundary

Target endpoints must use HTTPS. The runner resolves DNS and rejects loopback, private, link-local and other non-public addresses. Redirects are not followed and responses are capped at 1 MiB.

Endpoint credentials are encrypted with AES-256-GCM before persistence. TraceRAG API keys are stored only as SHA-256 hashes.

The Supabase schema enables RLS on every public table and scopes access through workspace/project membership.

## Web alpha

See `web/README.md`.

Required server configuration:

```text
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
SUPABASE_SECRET_KEY
TRACERAG_ENCRYPTION_KEY
```

Apply `supabase/schema.sql` to a dedicated Supabase project before running the hosted app.

## Core

```bash
uv sync
uv run python -c "from app.ingestao import indexar_documentos; print(indexar_documentos('data/documentos_teste', project_id='docs-demo'))"
uv run uvicorn app.main:app --reload
uv run python scripts/evaluate_retrieval.py --project-id docs-demo --k 3
```

## Product boundary

This is an alpha, not a claim of product-market fit. The milestone stops at:

```text
account → workspace → project → existing RAG endpoint
→ eval dataset → run → baseline comparison → CI pass/fail
```

Billing, queues, SSO, broad LLM observability, prompt management and enterprise administration stay outside this milestone until usage justifies them.

## Validation target

The first target users are small AI agencies, consultancies and product teams that maintain RAG systems and currently validate retrieval/answer changes manually.
