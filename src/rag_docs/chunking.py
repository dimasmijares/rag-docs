from __future__ import annotations

import hashlib
import json
import re

from rag_docs.contracts import IndexFingerprint
from rag_docs.models import DocumentCandidate, DocumentChunk, ExtractedUnit

# Bump when the windowing algorithm or its identity payload changes: it is one
# of the components IndexFingerprint covers (RULE-004).
CHUNKER_VERSION = "whitespace-window-v1"

TOKEN_PATTERN = re.compile(r"\S+")


def _windows(text: str, size: int, overlap: int) -> list[str]:
    matches = list(TOKEN_PATTERN.finditer(text))
    if not matches:
        return []
    if len(matches) <= size:
        return [text.strip()]
    step = size - overlap
    chunks: list[str] = []
    for start in range(0, len(matches), step):
        end = min(start + size, len(matches))
        char_start = matches[start].start()
        char_end = matches[end - 1].end()
        chunks.append(text[char_start:char_end].strip())
        if end == len(matches):
            break
    return chunks


def chunk_document(
    candidate: DocumentCandidate,
    units: list[ExtractedUnit],
    target_tokens: int = 500,
    overlap_tokens: int = 75,
    fingerprint: IndexFingerprint | None = None,
) -> list[DocumentChunk]:
    """Split ``units`` into token windows.

    ``content_hash`` is always part of a chunk's identity: different content at
    the same position produces a different point, so a rewrite no longer needs
    a delete before the upsert (``RULE-004``). When ``fingerprint`` is given,
    its digest is folded in too, so points from an incompatible pipeline
    configuration are never mistaken for the same identity.
    """
    if target_tokens < 1 or overlap_tokens < 0 or overlap_tokens >= target_tokens:
        raise ValueError("El tamaño debe ser positivo y el solape menor que el tamaño")

    chunks: list[DocumentChunk] = []
    for unit_index, unit in enumerate(units):
        for local_index, text in enumerate(_windows(unit.text, target_tokens, overlap_tokens)):
            global_index = len(chunks)
            identity_payload: dict[str, object] = {
                "document": candidate.document_id,
                "unit": unit_index,
                "local": local_index,
                "locator": unit.locator,
                "section": unit.section,
                "content_hash": candidate.content_hash,
            }
            if fingerprint is not None:
                identity_payload["fingerprint"] = fingerprint.digest()
            identity = json.dumps(identity_payload, sort_keys=True, ensure_ascii=False)
            chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=candidate.document_id,
                    source_id=candidate.source_id,
                    file_name=candidate.file_name,
                    original_uri=candidate.original_uri,
                    relative_path=candidate.relative_path,
                    content_hash=candidate.content_hash,
                    text=text,
                    locator=dict(unit.locator),
                    section=unit.section,
                    chunk_index=global_index,
                )
            )
    return chunks
