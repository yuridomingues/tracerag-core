"""Testes do pipeline RAG."""

from __future__ import annotations

from pathlib import Path

import app.embeddings as embeddings_module
import app.ingestao as ingestao_module
import app.rag as rag_module


def test_dividir_em_chunks_com_overlap() -> None:
    texto = "abcdefghij" * 20
    chunks = ingestao_module.dividir_em_chunks(texto, tamanho=50, sobreposicao=10)

    assert chunks
    assert all(len(chunk) <= 50 for chunk in chunks)
    assert chunks[0][-10:] == chunks[1][:10]


def test_colecoes_sao_derivadas_do_project_id() -> None:
    assert ingestao_module.nome_colecao("Docs Demo") == "tracerag-docs-demo"
    assert ingestao_module.nome_colecao("cliente/01") == "tracerag-cliente-01"


def test_buscar_contexto_em_indice_de_teste(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        embeddings_module,
        "gerar_embedding",
        lambda texto: [0.1, 0.2, 0.3],
        raising=False,
    )
    monkeypatch.setattr(
        rag_module, "gerar_embedding", lambda texto: [0.1, 0.2, 0.3], raising=False
    )
    monkeypatch.setattr(
        ingestao_module, "gerar_embedding", lambda texto: [0.1, 0.2, 0.3], raising=False
    )

    pasta = tmp_path / "docs"
    pasta.mkdir()
    (pasta / "rate_limit.txt").write_text(
        "A API aceita no maximo 100 requisicoes por minuto.", encoding="utf-8"
    )

    total = ingestao_module.indexar_documentos(str(pasta), project_id="teste")
    contexto = rag_module.buscar_contexto(
        "Qual e o limite da API?", k=1, project_id="teste"
    )

    assert total == 1
    assert contexto
    assert "100 requisicoes" in contexto[0]
