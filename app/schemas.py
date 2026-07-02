"""Modelos Pydantic para a API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DadosEmpresa(BaseModel):
    """Dados basicos da empresa analisada."""

    nome: str = Field(min_length=2, max_length=120)
    setor: str = Field(min_length=2, max_length=80)
    descricao: str = Field(min_length=20, max_length=1000)
    funcionarios: int = Field(ge=1, le=100000)


class RequisicaoAnalise(BaseModel):
    """Requisicao para gerar analise ESG."""

    dados_empresa: DadosEmpresa
    pergunta: str = Field(min_length=5, max_length=1000)


class RespostaAnalise(BaseModel):
    """Resposta produzida pela analise."""

    empresa: str
    recomendacao: str
    trechos_contexto_usados: list[str]
