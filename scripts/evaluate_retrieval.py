"""Executa benchmark de retrieval por projeto e imprime metricas em JSON."""

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
    parser = argparse.ArgumentParser(description="Avalia retrieval de um projeto TraceRAG.")
    parser.add_argument("--cases", type=Path, default=Path("data/eval_cases.jsonl"))
    parser.add_argument("--project-id", default="docs-demo")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--max-distance", type=float, default=None)
    args = parser.parse_args()

    casos = carregar_casos(args.cases)

    def recuperar(pergunta: str, k: int):
        return buscar_contexto_detalhado(
            pergunta,
            k=k,
            project_id=args.project_id,
            distancia_maxima=args.max_distance,
        )

    resultado = avaliar_recuperacao(casos, recuperar, k=args.k)
    print(
        json.dumps(
            {
                "project_id": args.project_id,
                "total_casos": resultado.total_casos,
                "k": args.k,
                "max_distance": args.max_distance,
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
