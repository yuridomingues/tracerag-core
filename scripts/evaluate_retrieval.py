"""Executa o benchmark local de recuperacao e imprime metricas em JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.evaluation import CasoAvaliacao, avaliar_recuperacao
from app.rag import buscar_contexto_detalhado


def carregar_casos(caminho: Path) -> list[CasoAvaliacao]:
    casos: list[CasoAvaliacao] = []
    for numero_linha, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), start=1):
        linha = linha.strip()
        if not linha:
            continue
        registro = json.loads(linha)
        try:
            casos.append(
                CasoAvaliacao(
                    identificador=str(registro["id"]),
                    pergunta=str(registro["pergunta"]),
                    origens_esperadas=tuple(registro["origens_esperadas"]),
                )
            )
        except KeyError as erro:
            raise ValueError(
                f"Caso invalido na linha {numero_linha}: campo ausente {erro}."
            ) from erro
    return casos


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia a recuperacao do indice RAG.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("data/eval_cases.jsonl"),
        help="Arquivo JSONL com perguntas e origens esperadas.",
    )
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    casos = carregar_casos(args.cases)
    resultado = avaliar_recuperacao(casos, buscar_contexto_detalhado, k=args.k)
    print(
        json.dumps(
            {
                "total_casos": resultado.total_casos,
                "k": args.k,
                "hit_rate": round(resultado.hit_rate, 4),
                "mrr": round(resultado.mrr, 4),
                "recall_origens": round(resultado.recall_origens, 4),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
