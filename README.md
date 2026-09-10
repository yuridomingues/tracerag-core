# Smart Impact IA

Prototipo minimo viavel da Frente de Desenvolvimento de Modelo do projeto Smart Impact IA. A proposta e analisar microempreendimentos da regiao serrana do Rio de Janeiro com LLM + RAG e gerar recomendacoes estruturadas alinhadas a ESG e ODS.

O repositorio tambem funciona como laboratorio de confiabilidade do pipeline: a recuperacao preserva proveniencia, a API reutiliza exatamente o contexto enviado ao LLM e o sistema possui um benchmark reproduzivel para detectar regressoes de retrieval.

## Fluxo

1. Documento entra no pipeline.
2. O texto e dividido em chunks.
3. Cada chunk vira embedding.
4. Os embeddings sao indexados no ChromaDB persistente com metadados de origem.
5. A pergunta da empresa chega pela API.
6. O sistema recupera os trechos relevantes uma unica vez.
7. O mesmo contexto e usado na resposta da API e no prompt do LLM.
8. Sem contexto recuperado, o pipeline se abstém e nao chama o LLM.
9. Com contexto, o LLM gera a recomendacao final.

## Instalacao

```bash
uv sync
```

## Configuracao

1. Copie `.env.example` para `.env`.
2. Ajuste `LLM_PROVIDER`, `OPENAI_API_KEY` e demais variaveis conforme o provedor escolhido.
3. Para OpenAI, `OPENAI_API_KEY` e obrigatoria.

## Indexacao

```bash
uv run python -c "from app.ingestao import indexar_documentos; indexar_documentos('data/documentos_teste')"
```

## Execucao da API

```bash
uv run uvicorn app.main:app --reload
```

## Testes

```bash
uv run pytest
```

## Avaliacao de retrieval

Depois de indexar `data/documentos_teste`:

```bash
uv run python scripts/evaluate_retrieval.py --k 3
```

O benchmark calcula `hit_rate`, `MRR` e `recall_origens` usando os casos declarados em `data/eval_cases.jsonl`.

A implementacao das metricas nao implica um resultado de qualidade por si so. Numeros devem ser registrados somente depois de executar o benchmark no ambiente e no modelo de embedding escolhidos. O protocolo e os limites estao em [`docs/evaluation.md`](docs/evaluation.md).

## Exemplo de requisicao

```bash
curl -X POST http://127.0.0.1:8000/analise/gerar ^
  -H "Content-Type: application/json" ^
  -d "{\"dados_empresa\": {\"nome\": \"Padaria Serra Verde\", \"setor\": \"alimentacao\", \"descricao\": \"Pequena padaria de bairro com foco em atendimento local e fornecedores regionais.\", \"funcionarios\": 6}, \"pergunta\": \"Quais acoes ESG devo priorizar?\"}"
```

## Limites atuais

O conjunto de avaliacao e pequeno e sintetico. Ele serve para regressao tecnica, nao para afirmar desempenho em producao. O sistema ainda precisa de casos revisados pela equipe, limiar de relevancia calibrado, avaliacao das citacoes, medicao de custo e latencia e testes de contexto adversarial antes de qualquer uso decisorio.
