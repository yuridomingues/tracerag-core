"""Metricas pequenas e reproduziveis para avaliar a recuperacao do RAG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from app.rag import TrechoRecuperado


@dataclass(frozen=True)
class CasoAvaliacao:
    """Pergunta de benchmark e documentos que deveriam sustentar a resposta."""

    identificador: str
    pergunta: str
    origens_esperadas: tuple[str, ...]


@dataclass(frozen=True)
class ResultadoAvaliacao:
    """Resumo agregado do benchmark de recuperacao."""

    total_casos: int
    hit_rate: float
    mrr: float
    recall_origens: float


def avaliar_recuperacao(
    casos: Iterable[CasoAvaliacao],
    buscar: Callable[[str, int], list[TrechoRecuperado]],
    k: int = 3,
) -> ResultadoAvaliacao:
    """Calcula hit rate, MRR e recall de origens em um conjunto de perguntas."""

    if k <= 0:
        raise ValueError("k deve ser maior que zero.")

    lista_casos = list(casos)
    if not lista_casos:
        return ResultadoAvaliacao(0, 0.0, 0.0, 0.0)

    hits = 0
    reciprocal_ranks = 0.0
    recalls: list[float] = []

    for caso in lista_casos:
        esperadas = {origem for origem in caso.origens_esperadas if origem}
        recuperados = buscar(caso.pergunta, k)
        origens = [trecho.origem for trecho in recuperados if trecho.origem]

        posicao_primeiro_acerto: int | None = None
        for posicao, origem in enumerate(origens, start=1):
            if origem in esperadas:
                posicao_primeiro_acerto = posicao
                break

        if posicao_primeiro_acerto is not None:
            hits += 1
            reciprocal_ranks += 1.0 / posicao_primeiro_acerto

        if esperadas:
            recalls.append(len(esperadas.intersection(origens)) / len(esperadas))
        else:
            recalls.append(1.0 if not origens else 0.0)

    total = len(lista_casos)
    return ResultadoAvaliacao(
        total_casos=total,
        hit_rate=hits / total,
        mrr=reciprocal_ranks / total,
        recall_origens=sum(recalls) / total,
    )
