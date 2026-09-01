from __future__ import annotations

from abc import ABC, abstractmethod

from rag_docs.models import DocumentCandidate


class DocumentSource(ABC):
    @property
    @abstractmethod
    def source_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def discover(self) -> list[DocumentCandidate]:
        """Return the current, deterministic snapshot of discoverable documents."""
        raise NotImplementedError
