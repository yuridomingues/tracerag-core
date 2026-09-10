"""Testes dos endpoints do TraceRAG Core."""

from __future__ import annotations

from fastapi.testclient import TestClient

import app.main as main_module
import app.routers.analise as api_module
from app.rag import TrechoRecuperado

client = TestClient(main_module.app)


def test_healthcheck() -> None:
    resposta = client.get("/v1/health")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "product": "tracerag-core"}


def test_validacao_de_payload_invalido() -> None:
    resposta = client.post("/v1/projects/demo/query", json={"pergunta": "x"})

    assert resposta.status_code == 422


def test_query_devolve_mesmas_evidencias_usadas_no_pipeline(monkeypatch) -> None:
    trechos = [
        TrechoRecuperado(
            texto="A API limita chamadas a 100 requisicoes por minuto.",
            origem="api_rate_limits.txt",
            chunk="0",
            distancia=0.08,
        )
    ]
    contexto_recebido: list[list[str]] = []

    monkeypatch.setattr(
        api_module,
        "buscar_contexto_detalhado",
        lambda pergunta, k, project_id, distancia_maxima: trechos,
    )

    def pipeline_mock(pergunta, contexto=None):
        contexto_recebido.append(contexto)
        return "O limite documentado e 100 requisicoes por minuto."

    monkeypatch.setattr(api_module, "pipeline_rag", pipeline_mock)

    resposta = client.post(
        "/v1/projects/docs-demo/query",
        json={"pergunta": "Qual e o limite da API?", "k": 3},
    )

    assert resposta.status_code == 200
    body = resposta.json()
    assert body["project_id"] == "docs-demo"
    assert body["abstencao"] is False
    assert body["evidencias"][0]["origem"] == "api_rate_limits.txt"
    assert body["evidencias"][0]["distancia"] == 0.08
    assert contexto_recebido == [[trechos[0].texto]]


def test_query_marca_abstencao_sem_evidencia(monkeypatch) -> None:
    monkeypatch.setattr(
        api_module,
        "buscar_contexto_detalhado",
        lambda pergunta, k, project_id, distancia_maxima: [],
    )

    resposta = client.post(
        "/v1/projects/docs-demo/query",
        json={"pergunta": "Pergunta sem resposta na base"},
    )

    assert resposta.status_code == 200
    assert resposta.json()["abstencao"] is True
    assert resposta.json()["evidencias"] == []
