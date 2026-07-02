"""Testes da abstracao do LLM."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.llm as llm_module


def test_chamar_llm_com_mock_openai(monkeypatch) -> None:
    """Garante que chamar_llm devolve o texto do mock da API."""

    resposta_mock = MagicMock()
    resposta_mock.choices[0].message.content = "Analise concluida."

    cliente_mock = MagicMock()
    cliente_mock.chat.completions.create.return_value = resposta_mock

    monkeypatch.setattr(
        llm_module, "OpenAI", MagicMock(return_value=cliente_mock), raising=False
    )
    monkeypatch.setattr(llm_module.time, "sleep", lambda *_: None)

    resultado = llm_module.chamar_llm([{"role": "user", "content": "teste"}])

    assert resultado == "Analise concluida."
