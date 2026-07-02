"""Abstracao de chamada ao modelo de linguagem."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.config import carregar_configuracoes

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - import opcional em ambiente reduzido
    OpenAI = None  # type: ignore

try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - import opcional em ambiente reduzido
    requests = None  # type: ignore

logger = logging.getLogger(__name__)


def _retry_delay(tentativa: int) -> float:
    return float(2**tentativa)


def _chamar_openai(mensagens: list[dict[str, Any]]) -> str:
    """Chama o SDK oficial da OpenAI."""

    if OpenAI is None:
        raise RuntimeError("Dependencia openai nao disponivel no ambiente.")

    configuracoes = carregar_configuracoes()
    cliente = OpenAI(api_key=configuracoes.openai_api_key)
    resposta = cliente.chat.completions.create(
        model=configuracoes.openai_model,
        messages=mensagens,
        temperature=0.2,
    )
    return (resposta.choices[0].message.content or "").strip()


def _chamar_ollama(mensagens: list[dict[str, Any]]) -> str:
    """Chama um servidor local do Ollama via HTTP."""

    if requests is None:
        raise RuntimeError("Dependencia requests nao disponivel no ambiente.")

    configuracoes = carregar_configuracoes()
    resposta = requests.post(
        f"{configuracoes.ollama_base_url.rstrip('/')}/api/chat",
        json={
            "model": configuracoes.ollama_model,
            "messages": mensagens,
            "stream": False,
            "options": {"temperature": 0.2},
        },
        timeout=60,
    )
    resposta.raise_for_status()
    dados = resposta.json()
    return str(dados.get("message", {}).get("content", "")).strip()


def chamar_llm(mensagens: list[dict[str, Any]]) -> str:
    """Chama o provedor de LLM configurado com retry exponencial."""

    configuracoes = carregar_configuracoes()
    ultimo_erro: Exception | None = None

    for tentativa in range(3):
        try:
            if configuracoes.llm_provider == "openai":
                resposta = _chamar_openai(mensagens)
            else:
                resposta = _chamar_ollama(mensagens)

            logger.info(
                "LLM respondeu com sucesso usando provedor %s.",
                configuracoes.llm_provider,
            )
            return resposta
        except Exception as erro:
            ultimo_erro = erro
            logger.exception("Falha ao chamar LLM na tentativa %s.", tentativa + 1)
            if tentativa < 2:
                time.sleep(_retry_delay(tentativa))

    raise RuntimeError(
        f"Falha ao chamar o LLM apos 3 tentativas: {ultimo_erro}"
    ) from ultimo_erro
