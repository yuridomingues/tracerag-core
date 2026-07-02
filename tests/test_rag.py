"""Testes do pipeline RAG."""

from __future__ import annotations

from pathlib import Path

import app.embeddings as embeddings_module
import app.ingestao as ingestao_module
import app.rag as rag_module


def test_dividir_em_chunks_com_overlap() -> None:
    """Verifica tamanho e sobreposicao dos chunks."""

    texto = "abcdefghij" * 20
    chunks = ingestao_module.dividir_em_chunks(texto, tamanho=50, sobreposicao=10)

    assert chunks
    assert all(len(chunk) <= 50 for chunk in chunks)
    assert chunks[0][-10:] == chunks[1][:10]


def test_buscar_contexto_em_indice_de_teste(monkeypatch, tmp_path: Path) -> None:
    """Valida busca de contexto em um indice pequeno."""

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
    (pasta / "doc1.txt").write_text(
        "Energia e residuos sao temas prioritarios.", encoding="utf-8"
    )

    ingestao_module.indexar_documentos(str(pasta))
    contexto = rag_module.buscar_contexto("Como melhorar energia?", k=1)

    assert contexto
    assert "Energia" in contexto[0]
