# Avaliação de retrieval

O benchmark mede a etapa de recuperação antes da geração. O objetivo é detectar regressões quando mudam embeddings, chunking, top-k ou thresholds.

## Métricas

- `hit_rate`: proporção de perguntas em que pelo menos uma origem esperada apareceu no top-k;
- `MRR`: posição do primeiro documento esperado, com peso maior para acertos no topo;
- `recall_origens`: fração das origens esperadas recuperadas por pergunta.

Essas métricas não provam que a resposta do LLM está correta. Elas medem somente retrieval.

## Dataset

Os casos ficam em `data/eval_cases.jsonl`. Cada linha contém uma pergunta e as fontes que deveriam sustentar a resposta. A base incluída é sintética e serve para regressão técnica.

## Execução

```bash
uv run python -c "from app.ingestao import indexar_documentos; indexar_documentos('data/documentos_teste', project_id='docs-demo')"
uv run python scripts/evaluate_retrieval.py --project-id docs-demo --k 3
```

Um threshold pode ser testado explicitamente:

```bash
uv run python scripts/evaluate_retrieval.py --project-id docs-demo --k 3 --max-distance 0.45
```

O valor de threshold deve ser calibrado com dados de avaliação. Não existe um número universalmente correto.

## Gate de CI futuro

A direção de produto é permitir que uma equipe registre um baseline e defina limites, por exemplo:

- `hit_rate` não pode cair mais de 3 pontos percentuais;
- `MRR` não pode cair abaixo do baseline configurado;
- perguntas críticas devem recuperar ao menos uma fonte obrigatória;
- casos não respondíveis devem continuar gerando abstensão.

O pipeline de CI deve falhar quando uma regressão ultrapassar o contrato do projeto.

## Limites atuais

Ainda faltam datasets maiores, avaliação de geração, custo, latência, adversarial retrieval e integração com um endpoint externo. O projeto não declara métricas de produção sem execução reproduzível.
