from dataclasses import replace
from pathlib import Path

import pytest

from rag_docs.chunking import chunk_document
from rag_docs.contracts import (
    SINGLE_TENANT_SCOPE,
    AclFields,
    AppError,
    ErrorKind,
    IndexFingerprint,
    IndexPublicationPort,
    Scope,
)
from rag_docs.models import DocumentCandidate, ExtractedUnit
from rag_docs.vector_store import QdrantVectorStore


def _fingerprint(**overrides: object) -> IndexFingerprint:
    defaults: dict[str, object] = dict(
        extractor="extractors-v1",
        chunker="whitespace-window-v1",
        chunk_tokens=500,
        chunk_overlap=75,
        embedding_model="intfloat/multilingual-e5-small",
        embedding_revision=None,
        dimension=3,
        normalize=True,
        query_prefix="query: ",
        passage_prefix="passage: ",
        payload_schema_version=2,
    )
    defaults.update(overrides)
    return IndexFingerprint(**defaults)  # type: ignore[arg-type]


def test_qdrant_adapter_with_in_memory_client(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("documentación técnica", encoding="utf-8")
    candidate = DocumentCandidate("demo", path, "doc.txt", path.as_uri(), "hash")
    fingerprint = _fingerprint()
    chunk = chunk_document(
        candidate, [ExtractedUnit("documentación técnica")], fingerprint=fingerprint
    )[0]
    store = QdrantVectorStore(":memory:", "test")

    store.ensure_collection(3, fingerprint)
    store.upsert([chunk], [[1.0, 0.0, 0.0]])

    documents = store.list_documents({"demo"})
    hits = store.search([1.0, 0.0, 0.0], limit=8, score_threshold=0.1, scope=SINGLE_TENANT_SCOPE)
    store.delete_document(candidate.document_id)

    assert candidate.document_id in documents
    assert hits[0].chunk.relative_path == "doc.txt"
    assert hits[0].score > 0.9
    assert store.list_documents({"demo"}) == {}


def test_ensure_collection_names_the_physical_collection_after_the_fingerprint() -> None:
    store = QdrantVectorStore(":memory:", "logical")
    fingerprint = _fingerprint()

    store.ensure_collection(3, fingerprint)

    assert store._resolve_alias() == f"logical__{fingerprint.digest()}"
    assert store.client.collection_exists(f"logical__{fingerprint.digest()}")


def test_ensure_collection_rejects_reuse_with_a_different_fingerprint() -> None:
    store = QdrantVectorStore(":memory:", "logical")
    store.ensure_collection(3, _fingerprint())

    with pytest.raises(AppError) as excinfo:
        store.ensure_collection(3, _fingerprint(chunk_tokens=600))

    assert excinfo.value.kind is ErrorKind.VALIDATION


def test_search_fails_explicitly_when_the_bound_fingerprint_no_longer_matches() -> None:
    store = QdrantVectorStore(":memory:", "logical")
    fingerprint = _fingerprint()
    store.ensure_collection(3, fingerprint)

    # Someone else's migration repointed the alias to another physical
    # collection without this process knowing: the next read must fail
    # explicitly (RULE-004), never degrade to whatever the alias now targets.
    other = _fingerprint(chunk_tokens=600)
    store._create_physical(store._physical_name(other), 3)
    store.publish_alias(store._physical_name(other))

    with pytest.raises(AppError) as excinfo:
        store.search([1.0, 0.0, 0.0], limit=8, score_threshold=None, scope=SINGLE_TENANT_SCOPE)

    assert excinfo.value.kind is ErrorKind.VALIDATION


def test_search_without_any_bound_fingerprint_is_rejected() -> None:
    store = QdrantVectorStore(":memory:", "logical")

    with pytest.raises(AppError):
        store.search([1.0, 0.0, 0.0], limit=8, score_threshold=None, scope=SINGLE_TENANT_SCOPE)


def test_publish_and_rollback_alias_keep_the_previous_collection_available() -> None:
    store = QdrantVectorStore(":memory:", "logical")
    first = _fingerprint()
    second = _fingerprint(chunk_tokens=600)
    store.ensure_collection(3, first)
    first_physical = store._physical_name(first)

    second_physical = store._physical_name(second)
    store._create_physical(second_physical, 3)
    store.publish_alias(second_physical)
    assert store._resolve_alias() == second_physical
    assert store.client.collection_exists(first_physical)  # rollback window

    store.rollback_alias(first_physical)
    assert store._resolve_alias() == first_physical


def test_qdrant_adapter_implements_the_publication_port() -> None:
    store = QdrantVectorStore(":memory:", "logical")
    fingerprint = _fingerprint()

    assert isinstance(store, IndexPublicationPort)
    assert store.logical_name == "logical"
    assert store.published_physical_name() is None

    store.ensure_collection(3, fingerprint)
    candidate = store.candidate_store(_fingerprint(chunk_tokens=600))
    candidate.ensure_collection(3, _fingerprint(chunk_tokens=600))

    # The alias still resolves to the published fingerprint; the candidate
    # exists only as its own physical collection.
    assert store.published_physical_name() == store.physical_name_for(fingerprint)
    assert candidate.collection_name == store.physical_name_for(_fingerprint(chunk_tokens=600))
    assert store.client.collection_exists(candidate.collection_name)


def test_rollback_fails_explicitly_once_the_previous_collection_is_gone() -> None:
    store = QdrantVectorStore(":memory:", "logical")
    store.ensure_collection(3, _fingerprint())

    with pytest.raises(AppError) as excinfo:
        store.rollback_alias("logical__never-existed")

    assert excinfo.value.kind is ErrorKind.NOT_FOUND


def test_prune_document_removes_only_stale_points(tmp_path: Path) -> None:
    fingerprint = _fingerprint()
    store = QdrantVectorStore(":memory:", "logical")
    store.ensure_collection(3, fingerprint)
    path = tmp_path / "doc.md"
    path.write_text("v1", encoding="utf-8")
    candidate_v1 = DocumentCandidate("demo", path, "doc.md", path.as_uri(), "hash-v1")
    old_chunks = chunk_document(
        candidate_v1,
        [ExtractedUnit("uno dos tres cuatro cinco")],
        target_tokens=2,
        overlap_tokens=0,
        fingerprint=fingerprint,
    )
    store.upsert(old_chunks, [[1.0, 0.0, 0.0] for _ in old_chunks])
    assert len(old_chunks) > 1

    candidate_v2 = DocumentCandidate("demo", path, "doc.md", path.as_uri(), "hash-v2")
    new_chunks = chunk_document(
        candidate_v2,
        [ExtractedUnit("uno dos tres cuatro cinco")],
        target_tokens=2,
        overlap_tokens=0,
        fingerprint=fingerprint,
    )
    store.upsert(new_chunks, [[1.0, 0.0, 0.0] for _ in new_chunks])
    store.prune_document(candidate_v2.document_id, {chunk.chunk_id for chunk in new_chunks})

    remaining = store.list_documents({"demo"})
    assert remaining[candidate_v2.document_id].content_hash == "hash-v2"
    hits = store.search([1.0, 0.0, 0.0], limit=50, score_threshold=None, scope=SINGLE_TENANT_SCOPE)
    assert {hit.chunk.chunk_id for hit in hits} == {chunk.chunk_id for chunk in new_chunks}


def test_ensure_collection_creates_acl_payload_indexes_before_any_write() -> None:
    # The local/in-memory Qdrant client accepts create_payload_index calls but
    # never materializes them in get_collection().payload_schema (it warns
    # "Payload indexes have no effect in the local Qdrant"), so this asserts
    # the call happens rather than inspecting schema state afterwards.
    store = QdrantVectorStore(":memory:", "logical")
    fingerprint = _fingerprint()
    indexed_fields: list[str] = []
    original = store.client.create_payload_index

    def spy(*, collection_name, field_name, field_schema):
        indexed_fields.append(field_name)
        return original(
            collection_name=collection_name, field_name=field_name, field_schema=field_schema
        )

    store.client.create_payload_index = spy

    store.ensure_collection(3, fingerprint)

    assert {"tenant_id", "acl_subjects", "classification"}.issubset(set(indexed_fields))


def test_search_prefilters_by_scope_and_denies_a_foreign_tenant(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("contenido", encoding="utf-8")
    candidate = DocumentCandidate("demo", path, "doc.txt", path.as_uri(), "hash")
    fingerprint = _fingerprint()
    chunk = chunk_document(candidate, [ExtractedUnit("contenido")], fingerprint=fingerprint)[0]
    store = QdrantVectorStore(":memory:", "test")
    store.ensure_collection(3, fingerprint)
    store.upsert([chunk], [[1.0, 0.0, 0.0]])

    same_tenant = store.search(
        [1.0, 0.0, 0.0], limit=8, score_threshold=None, scope=SINGLE_TENANT_SCOPE
    )
    other_tenant = store.search(
        [1.0, 0.0, 0.0],
        limit=8,
        score_threshold=None,
        scope=Scope(tenant="other-tenant"),
    )

    assert len(same_tenant) == 1
    assert other_tenant == []


def test_update_acl_changes_payload_without_touching_the_vector(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("contenido", encoding="utf-8")
    candidate = DocumentCandidate("demo", path, "doc.txt", path.as_uri(), "hash")
    fingerprint = _fingerprint()
    chunk = chunk_document(candidate, [ExtractedUnit("contenido")], fingerprint=fingerprint)[0]
    store = QdrantVectorStore(":memory:", "test")
    store.ensure_collection(3, fingerprint)
    store.upsert([chunk], [[1.0, 0.0, 0.0]])
    revoked = AclFields(
        tenant_id="other-tenant", acl_subjects=("other-tenant",), classification="internal"
    )

    store.update_acl(candidate.document_id, revoked)

    assert store.search(
        [1.0, 0.0, 0.0], limit=8, score_threshold=None, scope=SINGLE_TENANT_SCOPE
    ) == []
    other_tenant_scope = Scope(
        tenant="other-tenant",
        subjects=frozenset({"other-tenant"}),
        classifications=frozenset({"internal"}),
    )
    hits = store.search(
        [1.0, 0.0, 0.0], limit=8, score_threshold=None, scope=other_tenant_scope
    )
    assert len(hits) == 1
    assert hits[0].chunk.tenant_id == "other-tenant"


def test_scan_chunks_returns_full_chunks_respecting_scope(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("contenido", encoding="utf-8")
    candidate = DocumentCandidate("demo", path, "doc.txt", path.as_uri(), "hash")
    fingerprint = _fingerprint()
    chunk = chunk_document(candidate, [ExtractedUnit("contenido lexico")], fingerprint=fingerprint)[
        0
    ]
    store = QdrantVectorStore(":memory:", "test")
    store.ensure_collection(3, fingerprint)
    store.upsert([chunk], [[1.0, 0.0, 0.0]])

    same_tenant = store.scan_chunks(SINGLE_TENANT_SCOPE)
    other_tenant = store.scan_chunks(Scope(tenant="other-tenant"))

    assert len(same_tenant) == 1
    assert same_tenant[0].text == "contenido lexico"
    assert other_tenant == []


def test_chunk_default_acl_is_never_absent() -> None:
    chunk = chunk_document(
        DocumentCandidate("demo", Path("doc.txt"), "doc.txt", "file:///doc.txt", "hash"),
        [ExtractedUnit("contenido")],
    )[0]

    assert chunk.tenant_id
    assert chunk.acl_subjects

    with pytest.raises(ValueError, match="ACL"):
        replace(chunk, tenant_id="", acl_subjects=())
