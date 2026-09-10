"""Testes das metricas de avaliacao da recuperacao."""

from __future__ import annotations

from app.evaluation import CasoAvaliacao, avaliar_recuperacao
from app.rag import TrechoRecuperado


def test_avaliar_recuperacao_calcula_metricas() -> None:
    casos = [
        CasoAvaliacao("energia", "Como reduzir energia?", ("energia.txt",)),
        CasoAvaliacao("comunidade", "Como apoiar a comunidade?", ("ods.txt",)),
    ]

    resultados = {
        "Como reduzir energia?": [
            TrechoRecuperado("outro", origem="outro.txt"),
            TrechoRecuperado("energia", origem="energia.txt"),
        ],
        "Como apoiar a comunidade?": [
            TrechoRecuperado("comunidade", origem="ods.txt"),
        ],
    }

    def buscar(pergunta: str, k: int) -> list[TrechoRecuperado]:
        return resultados[pergunta][:k]

    resultado = avaliar_recuperacao(casos, buscar, k=2)

    assert resultado.total_casos == 2
    assert resultado.hit_rate == 1.0
    assert resultado.mrr == 0.75
    assert resultado.recall_origens == 1.0


def test_avaliar_recuperacao_sem_casos() -> None:
    resultado = avaliar_recuperacao([], lambda pergunta, k: [], k=3)

    assert resultado.total_casos == 0
    assert resultado.hit_rate == 0.0
