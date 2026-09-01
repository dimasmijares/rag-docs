from __future__ import annotations

import fnmatch
import hashlib
from pathlib import Path

from rag_docs.config import SourceDefinition
from rag_docs.models import DocumentCandidate
from rag_docs.sources.base import DocumentSource


def _matches(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        normalized_pattern = pattern.replace("\\", "/")
        if fnmatch.fnmatch(normalized, normalized_pattern):
            return True
        if normalized_pattern.startswith("**/") and fnmatch.fnmatch(
            normalized, normalized_pattern[3:]
        ):
            return True
    return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class LocalFolderSource(DocumentSource):
    def __init__(self, definition: SourceDefinition) -> None:
        self.definition = definition

    @property
    def source_id(self) -> str:
        return self.definition.id

    def discover(self) -> list[DocumentCandidate]:
        root = self.definition.root
        if not root.is_dir():
            raise FileNotFoundError(f"La raíz de la fuente '{self.source_id}' no existe: {root}")

        candidates: list[DocumentCandidate] = []
        for path in sorted(root.rglob("*"), key=lambda item: str(item).casefold()):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if not _matches(relative, self.definition.include):
                continue
            if _matches(relative, self.definition.exclude):
                continue
            candidates.append(
                DocumentCandidate(
                    source_id=self.source_id,
                    path=path.resolve(),
                    relative_path=relative,
                    original_uri=path.resolve().as_uri(),
                    content_hash=_sha256(path),
                )
            )
        return candidates
