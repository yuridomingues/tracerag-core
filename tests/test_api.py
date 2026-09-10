"""Testes dos endpoints da API."""

from __future__ import annotations

from fastapi.testclient import TestClient

import app.main as main_module
import app.routers.analise as analise_module

client = TestClient(main_module.app)


def test_healthcheck() -> None:
    """Verifica o healthcheck da API."""

    resposta = client.get("/analise/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_validacao_de_dados_invalidos() -> None:
    """Garante que dados invalidos retornam 422."""

    resposta = client.post("/analise/gerar", json={"dados_empresa": {"nome": "A"}})

    assert resposta.status_code == 422


def test_endpoint_gerar_com_mock_do_llm(monkeypatch) -> None:
    """Testa o endpoint principal sem chamar APIs reais."""

    contexto_esperado = ["Contexto ESG de teste."]
    contexto_recebido: list[list[str]] = []

    monkeypatch.setattr(
        analise_module, "buscar_contexto", lambda pergunta: contexto_esperado
    )

    def pipeline_mock(pergunta, dados_empresa, contexto=None):
        contexto_recebido.append(contexto)
        return "Plano de acao ESG mockado."

    monkeypatch.setattr(analise_module, "pipeline_rag", pipeline_mock)

    payload = {
        "dados_empresa": {
            "nome": "Padaria Serra Verde",
            "setor": "alimentacao",
            "descricao": "Pequena padaria de bairro com foco em atendimento local e fornecedores regionais.",
            "funcionarios": 6,
        },
        "pergunta": "Quais acoes ESG devo priorizar?",
    }

    resposta = client.post("/analise/gerar", json=payload)

    assert resposta.status_code == 200
    body = resposta.json()
    assert body["empresa"] == "Padaria Serra Verde"
    assert body["trechos_contexto_usados"] == contexto_esperado
    assert contexto_recebido == [contexto_esperado]
    assert "mockado" in body["recomendacao"]
