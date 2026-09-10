"""Regressoes de rastreabilidade e abstencao do pipeline RAG."""

from __future__ import annotations

import app.rag as rag_module


def test_busca_detalhada_preserva_origem_e_distancia(monkeypatch) -> None:
    class ColecaoFalsa:
        def query(self, **kwargs):
            return {
                "documents": [["Trecho sobre energia."]],
                "metadatas": [[{"origem": "energia.txt", "chunk": "2"}]],
                "distances": [[0.12]],
            }

    monkeypatch.setattr(rag_module, "_obter_colecao", lambda: ColecaoFalsa())
    monkeypatch.setattr(rag_module, "gerar_embedding", lambda texto: [0.1, 0.2])

    trechos = rag_module.buscar_contexto_detalhado("energia", k=1)

    assert len(trechos) == 1
    assert trechos[0].origem == "energia.txt"
    assert trechos[0].chunk == "2"
    assert trechos[0].distancia == 0.12


def test_pipeline_reutiliza_contexto_sem_nova_busca(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_module,
        "buscar_contexto",
        lambda pergunta: (_ for _ in ()).throw(AssertionError("busca duplicada")),
    )
    monkeypatch.setattr(rag_module, "chamar_llm", lambda mensagens: "resposta")

    resposta = rag_module.pipeline_rag(
        "pergunta",
        {"nome": "Empresa"},
        contexto=["trecho previamente recuperado"],
    )

    assert resposta == "resposta"


def test_pipeline_abstem_sem_contexto(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_module,
        "chamar_llm",
        lambda mensagens: (_ for _ in ()).throw(AssertionError("LLM nao deveria rodar")),
    )

    resposta = rag_module.pipeline_rag("pergunta", {"nome": "Empresa"}, contexto=[])

    assert resposta == rag_module.RESPOSTA_SEM_CONTEXTO
