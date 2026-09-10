"""Ingestao de documentos e indexacao no ChromaDB por projeto."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
import re

from app.config import carregar_configuracoes
from app.embeddings import gerar_embedding

try:
    import chromadb  # type: ignore
except Exception:  # pragma: no cover
    chromadb = None  # type: ignore

logger = logging.getLogger(__name__)

PREFIXO_COLECAO = "tracerag"


def normalizar_project_id(project_id: str) -> str:
    """Converte o identificador externo em um slug seguro para a colecao."""

    slug = re.sub(r"[^a-z0-9_-]+", "-", project_id.strip().lower()).strip("-_" )
    if not slug:
        raise ValueError("project_id invalido.")
    return slug[:48]


def nome_colecao(project_id: str = "default") -> str:
    return f"{PREFIXO_COLECAO}-{normalizar_project_id(project_id)}"


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


def obter_colecao(project_id: str = "default"):
    """Retorna a colecao persistente isolada logicamente por projeto."""

    if chromadb is None:
        raise RuntimeError("Dependencia chromadb nao disponivel no ambiente.")

    configuracoes = carregar_configuracoes()
    cliente = chromadb.PersistentClient(path=configuracoes.chroma_persist_dir)
    return cliente.get_or_create_collection(
        name=nome_colecao(project_id), metadata={"hnsw:space": "cosine"}
    )


def indexar_documentos(caminho_pasta: str, project_id: str = "default") -> int:
    """Indexa arquivos .txt com ids deterministas e proveniencia."""

    pasta = Path(caminho_pasta)
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta nao encontrada: {caminho_pasta}")

    colecao = obter_colecao(project_id)
    ids: list[str] = []
    documentos: list[str] = []
    embeddings: list[list[float]] = []
    metadados: list[dict[str, str]] = []

    for arquivo in sorted(pasta.glob("*.txt")):
        texto = arquivo.read_text(encoding="utf-8")
        for indice, chunk in enumerate(dividir_em_chunks(texto)):
            digest = hashlib.sha256(
                f"{arquivo.name}:{indice}:{chunk}".encode("utf-8")
            ).hexdigest()[:32]
            ids.append(digest)
            documentos.append(chunk)
            embeddings.append(gerar_embedding(chunk))
            metadados.append(
                {
                    "origem": arquivo.name,
                    "chunk": str(indice),
                    "project_id": normalizar_project_id(project_id),
                }
            )

    if not documentos:
        logger.warning("Nenhum documento .txt encontrado em %s.", caminho_pasta)
        return 0

    colecao.upsert(
        ids=ids, documents=documentos, embeddings=embeddings, metadatas=metadados
    )
    logger.info("Indexacao concluida com %s chunks no projeto %s.", len(documentos), project_id)
    return len(documentos)
