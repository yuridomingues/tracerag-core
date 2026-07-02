# Smart Impact IA

Prototipo minimo viavel da Frente de Desenvolvimento de Modelo do projeto Smart Impact IA. A proposta e analisar microempreendimentos da regiao serrana do Rio de Janeiro com LLM + RAG e gerar recomendacoes estruturadas alinhadas a ESG e ODS.

## Fluxo

1. Documento entra no pipeline.
2. O texto e dividido em chunks.
3. Cada chunk vira embedding.
4. Os embeddings sao indexados no ChromaDB persistente.
5. A pergunta da empresa chega pela API.
6. O sistema busca os chunks mais relevantes.
7. O prompt combina dados da empresa + contexto recuperado.
8. O LLM gera a recomendacao final.
9. A API devolve a resposta estruturada.

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

## Exemplo de requisicao

```bash
curl -X POST http://127.0.0.1:8000/analise/gerar ^
  -H "Content-Type: application/json" ^
  -d "{\"dados_empresa\": {\"nome\": \"Padaria Serra Verde\", \"setor\": \"alimentacao\", \"descricao\": \"Pequena padaria de bairro com foco em atendimento local e fornecedores regionais.\", \"funcionarios\": 6}, \"pergunta\": \"Quais acoes ESG devo priorizar?\"}"
```
