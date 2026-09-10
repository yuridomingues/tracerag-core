# Avaliacao do RAG

O objetivo deste benchmark e medir a etapa de recuperacao antes de discutir qualidade generativa. A base de teste e pequena de proposito: os casos servem para tornar regressao visivel, nao para sustentar uma conclusao estatistica sobre desempenho em producao.

## O que e medido

- `hit_rate`: proporcao de perguntas em que pelo menos uma origem esperada apareceu no top-k.
- `mrr`: posicao media do primeiro documento esperado, com peso maior para acertos no topo.
- `recall_origens`: fracao das origens esperadas recuperadas por pergunta.

Essas metricas avaliam retrieval. Elas nao provam que a resposta do LLM esta correta, completa ou segura.

## Casos

Os casos ficam em `data/eval_cases.jsonl`. Cada linha registra uma pergunta e os arquivos que deveriam sustentar a resposta. Os documentos atuais sao sinteticos e pertencem ao proprio repositorio.

## Como executar

Primeiro indexe a base de teste:

```bash
uv run python -c "from app.ingestao import indexar_documentos; indexar_documentos('data/documentos_teste')"
```

Depois rode:

```bash
uv run python scripts/evaluate_retrieval.py --k 3
```

O script imprime JSON para facilitar comparacao entre alteracoes de embedding, chunking e parametros de busca.

## Abstencao

O pipeline agora interrompe a geracao quando nenhum trecho e recuperado. Nesse caso, o LLM nao e chamado. Isso cria um comportamento deterministico para ausencia de evidencia e reduz o risco de produzir recomendacao sem base indexada.

Ainda falta definir um limiar de relevancia para distinguir "algum trecho foi recuperado" de "o trecho recuperado e suficientemente relevante". Esse limiar deve ser calibrado com um conjunto de avaliacao maior, em vez de ser escolhido por intuicao.

## Proximos experimentos

1. Ampliar o conjunto de perguntas com exemplos revisados pela equipe de pesquisa.
2. Separar casos respondiveis e nao respondiveis.
3. Medir custo e latencia por etapa.
4. Criar avaliacao de citacao: a recomendacao deve apontar quais trechos sustentam cada afirmacao relevante.
5. Testar documentos com instrucoes maliciosas ou irrelevantes para verificar se o contexto nao passa a controlar o comportamento do sistema.

Resultados numericos nao sao registrados aqui ate o benchmark ser executado em um ambiente configurado com o embedding escolhido.
