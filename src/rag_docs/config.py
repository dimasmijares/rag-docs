from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SUPPORTED_PATTERNS = [
    "**/*.pdf",
    "**/*.docx",
    "**/*.pptx",
    "**/*.xlsx",
    "**/*.txt",
    "**/*.md",
]


class SourceDefinition(BaseModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    type: Literal["local_folder"] = "local_folder"
    root: Path
    include: list[str] = Field(default_factory=lambda: list(SUPPORTED_PATTERNS))
    exclude: list[str] = Field(default_factory=lambda: ["**/~$*", "**/.*/**"])

    @field_validator("include")
    @classmethod
    def require_includes(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("include debe contener al menos un patrón")
        return value


class SourceFile(BaseModel):
    sources: list[SourceDefinition]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="RAG_DOCS_", env_file=".env", extra="ignore"
    )

    sources_file: Path = Path("config/sources.yaml")
    #: Vector backend implementation selected by the container factory
    #: (ADR-RAG-013). Only ``qdrant`` exists; new backends add a literal here.
    vector_backend: Literal["qdrant"] = "qdrant"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "rag_docs"
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_batch_size: int = 16
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_timeout: float = 180.0
    ollama_temperature: float = 0.0
    ollama_seed: int = 0
    ollama_active_profile: Literal["local", "remote"] = "local"
    ollama_local_url: str | None = None
    ollama_local_model: str | None = None
    ollama_remote_url: str | None = None
    ollama_remote_model: str | None = None
    retrieval_top_k: int = 8
    context_chunks: int = 5
    min_score: float = 0.45
    chunk_tokens: int = 500
    chunk_overlap: int = 75
    #: Cross-encoder reranking (WRK-TASK-038). ``None`` keeps v0.3.0 behavior
    #: unchanged — no model download, no added latency — even though a
    #: measured comparison showed a clean recall/MRR improvement on the
    #: validation gold set with no regression at any cutoff (see
    #: ADR-RAG-012). An operator opts in explicitly by setting this to a
    #: sentence-transformers cross-encoder model name, e.g.
    #: ``cross-encoder/mmarco-mMiniLMv2-L12-H384-v1``.
    reranker_model: str | None = None
    rerank_top_n: int | None = None


def load_sources(path: Path) -> list[SourceDefinition]:
    config_path = path.expanduser().resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"No existe el archivo de fuentes: {config_path}")
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    parsed = SourceFile.model_validate(raw)
    seen: set[str] = set()
    resolved: list[SourceDefinition] = []
    for source in parsed.sources:
        if source.id in seen:
            raise ValueError(f"ID de fuente duplicado: {source.id}")
        seen.add(source.id)
        root = source.root.expanduser()
        if not root.is_absolute():
            root = config_path.parent / root
        resolved.append(source.model_copy(update={"root": root.resolve()}))
    return resolved
