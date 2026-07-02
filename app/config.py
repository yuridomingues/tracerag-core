"""Configuracao central da aplicacao."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfiguracaoError(RuntimeError):
    """Erro de configuracao da aplicacao."""


class Configuracoes(BaseSettings):
    """Configuracoes carregadas do ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    llm_provider: Literal["openai", "ollama"] = "openai"
    openai_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"
    openai_embedding_model: str = "text-embedding-3-small"
    chroma_persist_dir: str = "chroma_db"
    openai_model: str = "gpt-4o-mini"
    ollama_model: str = "llama3.1"
    embedding_provider: Literal["sentence-transformers", "openai"] = (
        "sentence-transformers"
    )
    sentence_transformers_model: str = "all-MiniLM-L6-v2"

    def validar(self) -> Configuracoes:
        """Valida combinacoes basicas de configuracao."""

        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ConfiguracaoError(
                "OPENAI_API_KEY ausente: defina a variavel no .env quando LLM_PROVIDER=openai."
            )

        return self


@lru_cache(maxsize=1)
def carregar_configuracoes() -> Configuracoes:
    """Carrega e valida as configuracoes da aplicacao."""

    return Configuracoes().validar()
