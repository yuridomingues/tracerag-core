"""Endpoints de analise ESG."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.config import ConfiguracaoError
from app.rag import buscar_contexto, pipeline_rag
from app.schemas import RequisicaoAnalise, RespostaAnalise

router = APIRouter(prefix="/analise", tags=["analise"])
logger = logging.getLogger(__name__)


@router.get("/saude")
def saude() -> dict[str, str]:
    """Healthcheck da API."""

    return {"status": "ok"}


@router.post("/gerar", response_model=RespostaAnalise)
def gerar_analise(requisicao: RequisicaoAnalise) -> RespostaAnalise:
    """Gera uma analise ESG com suporte de RAG."""

    try:
        contexto = buscar_contexto(requisicao.pergunta)
    except Exception as erro:
        logger.exception("Erro ao consultar o banco vetorial.")
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao consultar o banco vetorial: {erro}",
        ) from erro

    try:
        recomendacao = pipeline_rag(
            pergunta=requisicao.pergunta,
            dados_empresa=requisicao.dados_empresa.model_dump(),
            contexto=contexto,
        )
        return RespostaAnalise(
            empresa=requisicao.dados_empresa.nome,
            recomendacao=recomendacao,
            trechos_contexto_usados=contexto,
        )
    except ConfiguracaoError as erro:
        logger.exception("Erro de configuracao durante analise.")
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    except Exception as erro:
        logger.exception("Falha ao gerar analise.")
        raise HTTPException(
            status_code=500,
            detail="Nao foi possivel gerar a analise ESG devido a uma falha no LLM.",
        ) from erro
