from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

Locator = dict[str, str | int]


@dataclass(frozen=True, slots=True)
class DocumentCandidate:
    source_id: str
    path: Path
    relative_path: str
    original_uri: str
    content_hash: str

    @property
    def document_id(self) -> str:
        import hashlib

        value = f"{self.source_id}:{self.relative_path.casefold()}"
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @property
    def file_name(self) -> str:
        return self.path.name


@dataclass(frozen=True, slots=True)
class ExtractedUnit:
    text: str
    locator: Locator = field(default_factory=dict)
    section: str | None = None


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    source_id: str
    file_name: str
    original_uri: str
    relative_path: str
    content_hash: str
    text: str
    locator: Locator
    section: str | None
    chunk_index: int

    def payload(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source_id": self.source_id,
            "file_name": self.file_name,
            "original_uri": self.original_uri,
            "relative_path": self.relative_path,
            "content_hash": self.content_hash,
            "text": self.text,
            "locator": self.locator,
            "section": self.section,
            "chunk_index": self.chunk_index,
        }


@dataclass(frozen=True, slots=True)
class IndexedDocument:
    document_id: str
    source_id: str
    content_hash: str


@dataclass(frozen=True, slots=True)
class SearchHit:
    chunk: DocumentChunk
    score: float


def chunk_from_payload(payload: dict[str, Any]) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=str(payload["chunk_id"]),
        document_id=str(payload["document_id"]),
        source_id=str(payload["source_id"]),
        file_name=str(payload["file_name"]),
        original_uri=str(payload["original_uri"]),
        relative_path=str(payload["relative_path"]),
        content_hash=str(payload["content_hash"]),
        text=str(payload["text"]),
        locator=dict(payload.get("locator") or {}),
        section=payload.get("section"),
        chunk_index=int(payload.get("chunk_index", 0)),
    )
