"""Endpoints do núcleo de consulta rastreável."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import ConfiguracaoError
from app.rag import RESPOSTA_SEM_CONTEXTO, buscar_contexto_detalhado, pipeline_rag
from app.schemas import EvidenciaRecuperada, RequisicaoConsulta, RespostaConsulta

router = APIRouter(prefix="/v1", tags=["rag"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "product": "tracerag-core"}


@router.post("/projects/{project_id}/query", response_model=RespostaConsulta)
def consultar(project_id: str, requisicao: RequisicaoConsulta) -> RespostaConsulta:
    """Consulta um projeto e devolve resposta junto das evidências recuperadas."""

    try:
        trechos = buscar_contexto_detalhado(
            requisicao.pergunta,
            k=requisicao.k,
            project_id=project_id,
            distancia_maxima=requisicao.distancia_maxima,
        )
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro)) from erro
    except Exception as erro:
        logger.exception("Falha ao consultar o indice vetorial.")
        raise HTTPException(status_code=500, detail="Falha ao consultar o indice vetorial.") from erro

    contexto = [trecho.texto for trecho in trechos]

    try:
        resposta = pipeline_rag(requisicao.pergunta, contexto=contexto)
    except ConfiguracaoError as erro:
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    except Exception as erro:
        logger.exception("Falha ao gerar resposta.")
        raise HTTPException(status_code=500, detail="Falha ao gerar resposta com o LLM.") from erro

    return RespostaConsulta(
        project_id=project_id,
        resposta=resposta,
        abstencao=resposta == RESPOSTA_SEM_CONTEXTO,
        evidencias=[
            EvidenciaRecuperada(
                texto=trecho.texto,
                origem=trecho.origem,
                chunk=trecho.chunk,
                distancia=trecho.distancia,
            )
            for trecho in trechos
        ],
    )
