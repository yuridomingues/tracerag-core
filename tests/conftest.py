"""Fixtures compartilhadas para os testes."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def configurar_ambiente_tmp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Configura ambiente isolado para testes."""

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "sentence-transformers")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("SENTENCE_TRANSFORMERS_MODEL", "all-MiniLM-L6-v2")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1")

    import app.config as config_module

    config_module.carregar_configuracoes.cache_clear()
    yield
    config_module.carregar_configuracoes.cache_clear()
