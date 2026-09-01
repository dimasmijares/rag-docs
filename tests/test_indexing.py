from pathlib import Path

from rag_docs.config import SourceDefinition
from rag_docs.indexing import IndexingService
from rag_docs.sources.local import LocalFolderSource
from tests.fakes import FakeEmbedder, FakeVectorStore


def test_indexing_is_incremental_and_deletes_removed_files(tmp_path: Path) -> None:
    path = tmp_path / "document.md"
    path.write_text("# Proceso\nPrimera versión", encoding="utf-8")
    source = LocalFolderSource(SourceDefinition(id="demo", root=tmp_path))
    store = FakeVectorStore()
    service = IndexingService([source], FakeEmbedder(), store)

    first = service.index()
    second = service.index()
    path.write_text("# Proceso\nVersión modificada", encoding="utf-8")
    third = service.index()
    path.unlink()
    fourth = service.index()

    assert (first.added, first.chunks_written) == (1, 1)
    assert second.unchanged == 1
    assert third.updated == 1
    assert fourth.deleted == 1
    assert store.documents == {}


def test_discovery_failure_does_not_delete_existing_index(tmp_path: Path) -> None:
    root = tmp_path / "docs"
    root.mkdir()
    path = root / "document.txt"
    path.write_text("contenido", encoding="utf-8")
    source = LocalFolderSource(SourceDefinition(id="demo", root=root))
    store = FakeVectorStore()
    service = IndexingService([source], FakeEmbedder(), store)
    service.index()
    root.rename(tmp_path / "unavailable")

    report = service.index()

    assert report.errors
    assert report.deleted == 0
    assert store.documents
