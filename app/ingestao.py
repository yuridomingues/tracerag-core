"""Ingestao de documentos e indexacao no ChromaDB."""

from __future__ import annotations

import logging
from pathlib import Path

from app.config import carregar_configuracoes
from app.embeddings import gerar_embedding

try:
    import chromadb  # type: ignore
except Exception:  # pragma: no cover - import opcional em ambiente reduzido
    chromadb = None  # type: ignore

logger = logging.getLogger(__name__)

NOME_COLECAO = "smart_impact_ia"


def dividir_em_chunks(
    texto: str, tamanho: int = 500, sobreposicao: int = 50
) -> list[str]:
    """Divide um texto em chunks com sobreposicao configuravel."""

    if tamanho <= 0:
        raise ValueError("tamanho deve ser maior que zero.")
    if sobreposicao < 0:
        raise ValueError("sobreposicao nao pode ser negativa.")
    if sobreposicao >= tamanho:
        raise ValueError("sobreposicao deve ser menor que tamanho.")

    texto = texto.strip()
    if not texto:
        return []

    chunks: list[str] = []
    passo = tamanho - sobreposicao

    for inicio in range(0, len(texto), passo):
        pedaco = texto[inicio : inicio + tamanho].strip()
        if pedaco:
            chunks.append(pedaco)
        if inicio + tamanho >= len(texto):
            break

    return chunks


def _obter_colecao():
    """Retorna ou cria a colecao persistente do ChromaDB."""

    if chromadb is None:
        raise RuntimeError("Dependencia chromadb nao disponivel no ambiente.")

    configuracoes = carregar_configuracoes()
    cliente = chromadb.PersistentClient(path=configuracoes.chroma_persist_dir)
    return cliente.get_or_create_collection(
        name=NOME_COLECAO, metadata={"hnsw:space": "cosine"}
    )


def indexar_documentos(caminho_pasta: str) -> None:
    """Le e indexa documentos .txt em uma colecao persistente do ChromaDB."""

    pasta = Path(caminho_pasta)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta nao encontrada: {caminho_pasta}")

    colecao = _obter_colecao()
    ids: list[str] = []
    documentos: list[str] = []
    embeddings: list[list[float]] = []
    metadados: list[dict[str, str]] = []

    for arquivo in sorted(pasta.glob("*.txt")):
        texto = arquivo.read_text(encoding="utf-8")
        for indice, chunk in enumerate(dividir_em_chunks(texto)):
            ids.append(f"{arquivo.stem}-{indice}")
            documentos.append(chunk)
            embeddings.append(gerar_embedding(chunk))
            metadados.append({"origem": arquivo.name, "chunk": str(indice)})

    if not documentos:
        logger.warning(
            "Nenhum documento .txt encontrado para indexacao em %s.", caminho_pasta
        )
        return

    colecao.upsert(
        ids=ids, documents=documentos, embeddings=embeddings, metadatas=metadados
    )
    logger.info("Indexacao concluida com %s chunks.", len(documentos))
