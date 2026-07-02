"""Aplicacao principal FastAPI."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.routers.analise import router as analise_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Smart Impact IA",
    description=(
        "API experimental para analise de microempreendimentos com LLM + RAG, "
        "focada em recomendacoes ESG e ODS."
    ),
    version="0.1.0",
)

app.include_router(analise_router)
