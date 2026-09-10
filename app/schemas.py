"""Contratos da API TraceRAG."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RequisicaoConsulta(BaseModel):
    pergunta: str = Field(min_length=3, max_length=2000)
    k: int = Field(default=3, ge=1, le=20)
    distancia_maxima: float | None = Field(default=None, ge=0)


class EvidenciaRecuperada(BaseModel):
    texto: str
    origem: str | None = None
    chunk: str | None = None
    distancia: float | None = None


class RespostaConsulta(BaseModel):
    project_id: str
    resposta: str
    abstencao: bool
    evidencias: list[EvidenciaRecuperada]
