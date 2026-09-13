from pathlib import Path

import pytest

from rag_docs import indexing
from rag_docs.config import SourceDefinition
from rag_docs.contracts import AppError
from rag_docs.indexing import PAYLOAD_SCHEMA_VERSION, IndexingService, migrate_and_publish
from rag_docs.sources.local import LocalFolderSource
from rag_docs.vector_store import QdrantVectorStore
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


def test_a_document_whose_acl_cannot_be_normalized_is_never_indexed(tmp_path: Path) -> None:
    path = tmp_path / "document.md"
    path.write_text("contenido corporativo", encoding="utf-8")
    source = LocalFolderSource(SourceDefinition(id="demo", root=tmp_path))
    store = FakeVectorStore()
    service = IndexingService(
        [source], FakeEmbedder(), store, acl_resolver=lambda candidate: None
    )

    report = service.index()

    assert report.skipped == 1
    assert report.added == 0
    assert report.errors and "ACL" in report.errors[0].message
    assert store.documents == {}


def test_indexed_chunks_carry_the_resolved_acl(tmp_path: Path) -> None:
    from rag_docs.contracts import AclFields

    path = tmp_path / "document.md"
    path.write_text("contenido corporativo", encoding="utf-8")
    source = LocalFolderSource(SourceDefinition(id="demo", root=tmp_path))
    store = FakeVectorStore()
    acl = AclFields(tenant_id="acme", acl_subjects=("group:eng",), classification="restricted")
    service = IndexingService([source], FakeEmbedder(), store, acl_resolver=lambda candidate: acl)

    service.index()

    (document_id,) = store.documents
    written = store.chunks[document_id]
    assert written and all(chunk.tenant_id == "acme" for chunk in written)
    assert all(chunk.acl_subjects == ("group:eng",) for chunk in written)
    assert all(chunk.classification == "restricted" for chunk in written)


def test_introducing_the_acl_payload_schema_forces_a_new_fingerprint() -> None:
    fingerprint = IndexingService([], FakeEmbedder(), FakeVectorStore()).fingerprint
    from dataclasses import replace

    pre_acl_equivalent = replace(fingerprint, payload_schema_version=PAYLOAD_SCHEMA_VERSION - 1)

    assert fingerprint.payload_schema_version == PAYLOAD_SCHEMA_VERSION
    assert fingerprint.digest() != pre_acl_equivalent.digest()


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


def test_migrate_and_publish_only_moves_the_alias_after_validation(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_text("contenido", encoding="utf-8")
    source = LocalFolderSource(SourceDefinition(id="demo", root=tmp_path))
    store = QdrantVectorStore(":memory:", "logical")
    IndexingService([source], FakeEmbedder(), store).index()
    previous_physical = store._resolve_alias()

    migrated = IndexingService(
        [source], FakeEmbedder(), store, chunk_tokens=10, chunk_overlap=2
    )
    seen_reports = []

    def validate(report, candidate_store) -> bool:
        seen_reports.append(report)
        return True

    physical = migrate_and_publish(migrated, validate)

    assert physical == store.physical_name_for(migrated.fingerprint)
    assert physical != previous_physical
    assert store._resolve_alias() == physical
    assert seen_reports and seen_reports[0].added == 1
    # The rollback window: the previous physical collection is untouched.
    assert store.client.collection_exists(previous_physical)


def test_migrate_and_publish_leaves_the_alias_untouched_when_validation_fails(
    tmp_path: Path,
) -> None:
    path = tmp_path / "doc.md"
    path.write_text("contenido", encoding="utf-8")
    source = LocalFolderSource(SourceDefinition(id="demo", root=tmp_path))
    store = QdrantVectorStore(":memory:", "logical")
    IndexingService([source], FakeEmbedder(), store).index()
    previous_physical = store._resolve_alias()

    migrated = IndexingService(
        [source], FakeEmbedder(), store, chunk_tokens=10, chunk_overlap=2
    )

    with pytest.raises(AppError):
        migrate_and_publish(migrated, lambda report, candidate_store: False)

    assert store._resolve_alias() == previous_physical


def test_migrate_and_publish_rejects_a_store_without_publication_port() -> None:
    live = IndexingService([], FakeEmbedder(), FakeVectorStore())

    with pytest.raises(AppError) as excinfo:
        migrate_and_publish(live, lambda report, candidate_store: True)

    assert "IndexPublicationPort" in excinfo.value.message


def test_indexing_module_does_not_depend_on_the_qdrant_adapter() -> None:
    # ADR-RAG-013: indexing and migration consume ports only.
    source = Path(indexing.__file__).read_text(encoding="utf-8")
    assert "vector_store" not in source
    assert "QdrantVectorStore" not in source
