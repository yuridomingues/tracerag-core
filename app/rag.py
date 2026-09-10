"""Pipeline RAG com retrieval rastreavel e abstencao explicita."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from app.embeddings import gerar_embedding
from app.ingestao import obter_colecao
from app.llm import chamar_llm

logger = logging.getLogger(__name__)

RESPOSTA_SEM_CONTEXTO = (
    "Nao ha evidencia suficiente na base indexada para responder com seguranca."
)


@dataclass(frozen=True)
class TrechoRecuperado:
    texto: str
    origem: str | None = None
    chunk: str | None = None
    distancia: float | None = None


def buscar_contexto_detalhado(
    pergunta: str,
    k: int = 3,
    project_id: str = "default",
    distancia_maxima: float | None = None,
) -> list[TrechoRecuperado]:
    """Busca evidencias preservando origem, chunk e distancia."""

    if k <= 0:
        raise ValueError("k deve ser maior que zero.")
    if distancia_maxima is not None and distancia_maxima < 0:
        raise ValueError("distancia_maxima nao pode ser negativa.")

    colecao = obter_colecao(project_id)
    embedding_pergunta = gerar_embedding(pergunta)
    resultado = colecao.query(query_embeddings=[embedding_pergunta], n_results=k)

    documentos = resultado.get("documents", [[]])[0] or []
    metadados = resultado.get("metadatas", [[]])[0] or []
    distancias = resultado.get("distances", [[]])[0] or []

    trechos: list[TrechoRecuperado] = []
    for indice, documento in enumerate(documentos):
        if not documento:
            continue

        metadata = metadados[indice] if indice < len(metadados) else None
        metadata = metadata if isinstance(metadata, dict) else {}
        distancia = distancias[indice] if indice < len(distancias) else None
        distancia_float = float(distancia) if distancia is not None else None

        if (
            distancia_maxima is not None
            and distancia_float is not None
            and distancia_float > distancia_maxima
        ):
            continue

        trechos.append(
            TrechoRecuperado(
                texto=str(documento),
                origem=str(metadata["origem"]) if metadata.get("origem") else None,
                chunk=str(metadata["chunk"]) if metadata.get("chunk") is not None else None,
                distancia=distancia_float,
            )
        )

    return trechos


def buscar_contexto(
    pergunta: str,
    k: int = 3,
    project_id: str = "default",
    distancia_maxima: float | None = None,
) -> list[str]:
    return [
        trecho.texto
        for trecho in buscar_contexto_detalhado(
            pergunta,
            k=k,
            project_id=project_id,
            distancia_maxima=distancia_maxima,
        )
    ]


def pipeline_rag(pergunta: str, contexto: list[str] | None = None) -> str:
    """Gera resposta somente a partir do contexto explicitamente fornecido."""

    if contexto is None:
        contexto = buscar_contexto(pergunta)

    if not contexto:
        logger.info("Geracao interrompida por ausencia de evidencia recuperada.")
        return RESPOSTA_SEM_CONTEXTO

    prompt_sistema = (
        "Voce responde perguntas sobre uma base de conhecimento privada. "
        "Use somente o contexto fornecido. Nao complete lacunas com conhecimento externo. "
        "Quando a evidencia nao sustentar uma afirmacao, deixe a limitacao explicita."
    )
    prompt_usuario = (
        f"Pergunta: {pergunta}\n\n"
        "Evidencias recuperadas:\n- " + "\n- ".join(contexto)
    )

    resposta = chamar_llm(
        [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario},
        ]
    )
    logger.info("Pipeline RAG finalizado.")
    return resposta
