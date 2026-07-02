"""Pipeline RAG para recuperacao de contexto e geracao de resposta."""

from __future__ import annotations

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


def _obter_colecao():
    """Retorna ou cria a colecao persistente do ChromaDB."""

    if chromadb is None:
        raise RuntimeError("Dependencia chromadb nao disponivel no ambiente.")

    configuracoes = carregar_configuracoes()
    cliente = chromadb.PersistentClient(path=configuracoes.chroma_persist_dir)
    return cliente.get_or_create_collection(
        name=NOME_COLECAO, metadata={"hnsw:space": "cosine"}
    )


def buscar_contexto(pergunta: str, k: int = 3) -> list[str]:
    """Busca trechos relevantes no ChromaDB para uma pergunta."""

    logger.info("Iniciando busca de contexto para pergunta: %s", pergunta)
    colecao = _obter_colecao()
    embedding_pergunta = gerar_embedding(pergunta)
    resultado = colecao.query(query_embeddings=[embedding_pergunta], n_results=k)
    documentos = resultado.get("documents", [[]])[0]
    return [str(documento) for documento in documentos if documento]


def pipeline_rag(pergunta: str, dados_empresa: dict) -> str:
    """Monta o prompt com contexto recuperado e chama o LLM."""

    contexto = buscar_contexto(pergunta)
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
