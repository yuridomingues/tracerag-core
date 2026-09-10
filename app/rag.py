"""Pipeline RAG para recuperacao de contexto e geracao de resposta."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from app.config import carregar_configuracoes
from app.embeddings import gerar_embedding
from app.ingestao import NOME_COLECAO
from app.llm import chamar_llm

try:
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - import opcional em ambiente reduzido
    chromadb = None  # type: ignore

logger = logging.getLogger(__name__)

RESPOSTA_SEM_CONTEXTO = (
    "Nao ha contexto suficiente na base indexada para responder com seguranca."
)


@dataclass(frozen=True)
class TrechoRecuperado:
    """Trecho retornado pelo indice com proveniencia quando disponivel."""

    texto: str
    origem: str | None = None
    chunk: str | None = None
    distancia: float | None = None


def _obter_colecao():
    """Retorna ou cria a colecao persistente do ChromaDB."""

    if chromadb is None:
        raise RuntimeError("Dependencia chromadb nao disponivel no ambiente.")

    configuracoes = carregar_configuracoes()
    cliente = chromadb.PersistentClient(path=configuracoes.chroma_persist_dir)
    return cliente.get_or_create_collection(
        name=NOME_COLECAO, metadata={"hnsw:space": "cosine"}
    )


def buscar_contexto_detalhado(pergunta: str, k: int = 3) -> list[TrechoRecuperado]:
    """Busca trechos relevantes preservando metadados de origem e distancia."""

    if k <= 0:
        raise ValueError("k deve ser maior que zero.")

    logger.info("Iniciando busca de contexto para pergunta: %s", pergunta)
    colecao = _obter_colecao()
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

        trechos.append(
            TrechoRecuperado(
                texto=str(documento),
                origem=str(metadata["origem"]) if metadata.get("origem") else None,
                chunk=str(metadata["chunk"]) if metadata.get("chunk") is not None else None,
                distancia=float(distancia) if distancia is not None else None,
            )
        )

    return trechos


def buscar_contexto(pergunta: str, k: int = 3) -> list[str]:
    """Busca apenas o texto dos trechos para manter compatibilidade com a API."""

    return [trecho.texto for trecho in buscar_contexto_detalhado(pergunta, k=k)]


def pipeline_rag(
    pergunta: str,
    dados_empresa: dict,
    contexto: list[str] | None = None,
) -> str:
    """Monta o prompt e chama o LLM usando exatamente o contexto informado."""

    if contexto is None:
        contexto = buscar_contexto(pergunta)

    if not contexto:
        logger.info("Analise interrompida por ausencia de contexto recuperado.")
        return RESPOSTA_SEM_CONTEXTO

    prompt_sistema = (
        "Voce e um assistente especializado em analise ESG para microempreendimentos. "
        "Responda apenas com base no contexto fornecido; se nao souber, diga que nao ha dados suficientes."
    )
    prompt_usuario = (
        f"Dados da empresa: {dados_empresa}\n\n"
        f"Pergunta: {pergunta}\n\n"
        f"Contexto recuperado:\n- " + "\n- ".join(contexto)
    )

    mensagens = [
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": prompt_usuario},
    ]
    resposta = chamar_llm(mensagens)
    logger.info("Pipeline RAG finalizado com sucesso.")
    return resposta
