# TraceRAG Core

Núcleo experimental para testar regressões em sistemas RAG com foco em retrieval verificável.

O projeto nasceu da necessidade de responder perguntas simples que muitas aplicações de IA não conseguem responder bem: qual fonte sustentou a resposta, qual chunk foi recuperado, quanto esse retrieval mudou depois de trocar embedding ou chunking e quando o sistema deveria se recusar a responder.

O objetivo não é competir com plataformas completas de observabilidade. O recorte é menor: regression testing de retrieval, evidência por consulta e uma API simples que pode ser colocada em CI.

## O que existe hoje

- coleções separadas por `project_id`;
- ingestão idempotente de documentos `.txt` com IDs determinísticos;
- retrieval com origem, chunk e distância;
- limiar opcional de distância para rejeitar evidência fraca;
- abstensão determinística quando não há contexto suficiente;
- benchmark com `hit_rate`, `MRR` e `recall_origens`;
- API FastAPI que devolve resposta e evidências usadas;
- testes automatizados e GitHub Actions.

## Fluxo

```text
Documentos
   ↓
chunking + embeddings
   ↓
coleção do projeto
   ↓
retrieval
   ↓
evidências + distância
   ↓
threshold opcional
   ↓
resposta ou abstensão
```

## Instalação

```bash
uv sync
```

Copie `.env.example` para `.env` e configure o provedor desejado.

## Indexar um projeto

```bash
uv run python -c "from app.ingestao import indexar_documentos; print(indexar_documentos('data/documentos_teste', project_id='docs-demo'))"
```

## Rodar API

```bash
uv run uvicorn app.main:app --reload
```

Healthcheck:

```bash
curl http://127.0.0.1:8000/v1/health
```

Consulta:

```bash
curl -X POST http://127.0.0.1:8000/v1/projects/docs-demo/query \
  -H 'Content-Type: application/json' \
  -d '{"pergunta":"Qual é o limite de requisições da API?","k":3,"distancia_maxima":0.45}'
```

A resposta inclui `abstencao` e a lista de `evidencias` com origem, chunk e distância.

## Benchmark

Depois de indexar a base de teste:

```bash
uv run python scripts/evaluate_retrieval.py --project-id docs-demo --k 3
```

Para testar um threshold:

```bash
uv run python scripts/evaluate_retrieval.py --project-id docs-demo --k 3 --max-distance 0.45
```

Os números só devem ser registrados depois de executar o benchmark com o embedding e a base que realmente serão usados. Um threshold não deve ser escolhido por intuição.

## Direção de produto

A hipótese comercial é oferecer uma camada simples de regression testing para equipes pequenas que já possuem RAG, mas ainda validam mudanças manualmente.

O produto futuro pode receber um endpoint do cliente ou SDK, executar um dataset de perguntas, comparar retrieval entre versões e bloquear um deploy quando uma mudança ultrapassar os limites configurados.

Isso ainda não é um SaaS pronto. Antes de produção faltam autenticação, isolamento forte de tenants, armazenamento gerenciado, política de retenção, rate limiting, billing e observabilidade operacional. Essas lacunas estão documentadas em `docs/saas-readiness.md`.

## Limites

A base incluída é sintética e serve apenas para regressão técnica. As métricas atuais medem retrieval, não provam correção factual da resposta final nem segurança do modelo.
