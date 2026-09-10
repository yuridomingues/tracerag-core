"""Aplicacao principal FastAPI do TraceRAG Core."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from app.routers.analise import router as rag_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="TraceRAG Core",
    description=(
        "Nucleo experimental para regression testing de RAG, com retrieval rastreavel, "
        "abstencao e evidencias por projeto."
    ),
    version="0.2.0",
)

app.include_router(rag_router)
