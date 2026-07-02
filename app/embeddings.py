"""Geração de embeddings para o pipeline RAG."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from app.config import carregar_configuracoes

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - import opcional em ambiente reduzido
    OpenAI = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover - import opcional em ambiente reduzido
    SentenceTransformer = None  # type: ignore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _carregar_modelo_sentence_transformers() -> Any:
    """Carrega o modelo local de embeddings."""

    if SentenceTransformer is None:
        raise RuntimeError(
            "Dependencia sentence-transformers nao disponivel no ambiente."
        )

    configuracoes = carregar_configuracoes()
    return SentenceTransformer(configuracoes.sentence_transformers_model)


def _gerar_embedding_openai(texto: str) -> list[float]:
    """Gera embedding usando a API da OpenAI."""

    if OpenAI is None:
        raise RuntimeError("Dependencia openai nao disponivel no ambiente.")

    configuracoes = carregar_configuracoes()
    cliente = OpenAI(api_key=configuracoes.openai_api_key)
    resposta = cliente.embeddings.create(
        model=configuracoes.openai_embedding_model, input=texto
    )
    return list(resposta.data[0].embedding)


def gerar_embedding(texto: str) -> list[float]:
    """Gera embedding para um texto usando o provedor configurado."""

    configuracoes = carregar_configuracoes()
    if configuracoes.embedding_provider == "openai":
        return _gerar_embedding_openai(texto)

    modelo = _carregar_modelo_sentence_transformers()
    embedding = modelo.encode(texto, normalize_embeddings=True)
    logger.debug("Embedding gerado com sentence-transformers.")
    return embedding.tolist()
