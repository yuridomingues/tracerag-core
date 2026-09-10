"""Regressoes de rastreabilidade, threshold e abstencao."""

from __future__ import annotations

import app.rag as rag_module


def test_busca_detalhada_preserva_origem_distancia_e_projeto(monkeypatch) -> None:
    projetos: list[str] = []

    class ColecaoFalsa:
        def query(self, **kwargs):
            return {
                "documents": [["Trecho sobre limite da API."]],
                "metadatas": [[{"origem": "api_rate_limits.txt", "chunk": "2"}]],
                "distances": [[0.12]],
            }

    def obter_colecao_mock(project_id):
        projetos.append(project_id)
        return ColecaoFalsa()

    monkeypatch.setattr(rag_module, "obter_colecao", obter_colecao_mock)
    monkeypatch.setattr(rag_module, "gerar_embedding", lambda texto: [0.1, 0.2])

    trechos = rag_module.buscar_contexto_detalhado(
        "qual e o limite?", k=1, project_id="docs-demo"
    )

    assert projetos == ["docs-demo"]
    assert len(trechos) == 1
    assert trechos[0].origem == "api_rate_limits.txt"
    assert trechos[0].chunk == "2"
    assert trechos[0].distancia == 0.12


def test_threshold_remove_evidencia_distante(monkeypatch) -> None:
    class ColecaoFalsa:
        def query(self, **kwargs):
            return {
                "documents": [["Trecho pouco relacionado."]],
                "metadatas": [[{"origem": "misc.txt", "chunk": "0"}]],
                "distances": [[0.71]],
            }

    monkeypatch.setattr(rag_module, "obter_colecao", lambda project_id: ColecaoFalsa())
    monkeypatch.setattr(rag_module, "gerar_embedding", lambda texto: [0.1, 0.2])

    trechos = rag_module.buscar_contexto_detalhado(
        "pergunta", k=1, project_id="demo", distancia_maxima=0.4
    )

    assert trechos == []


def test_pipeline_reutiliza_contexto_sem_nova_busca(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_module,
        "buscar_contexto",
        lambda pergunta: (_ for _ in ()).throw(AssertionError("busca duplicada")),
    )
    monkeypatch.setattr(rag_module, "chamar_llm", lambda mensagens: "resposta")

    resposta = rag_module.pipeline_rag(
        "pergunta", contexto=["trecho previamente recuperado"]
    )

    assert resposta == "resposta"


def test_pipeline_abstem_sem_contexto(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_module,
        "chamar_llm",
        lambda mensagens: (_ for _ in ()).throw(AssertionError("LLM nao deveria rodar")),
    )

    resposta = rag_module.pipeline_rag("pergunta", contexto=[])

    assert resposta == rag_module.RESPOSTA_SEM_CONTEXTO
