"""Contract every ``VectorStorePort`` + ``IndexPublicationPort`` backend must pass
(``ADR-RAG-013``, ``WRK-TASK-096``).

Only port methods are used here, never adapter internals, so a new backend is
accepted by this suite rather than by inspection. The ``contract_store`` fixture
(``tests/conftest.py``) runs it against Qdrant ``:memory:`` by default and, only
when ``RAG_DOCS_CONTRACT_LIVE_FACTORY`` is set, against a live backend too.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rag_docs.chunking import chunk_document
from rag_docs.contracts import (
    SINGLE_TENANT_SCOPE,
    AclFields,
    AppError,
    DocumentCandidate,
    DocumentChunk,
    ErrorKind,
    ExtractedUnit,
    IndexPublicationPort,
    Scope,
)

VECTOR = [1.0, 0.0, 0.0]
OTHER_TENANT_ACL = AclFields(
    tenant_id="other-tenant", acl_subjects=("other-tenant",), classification="internal"
)
OTHER_TENANT_SCOPE = Scope(
    tenant="other-tenant",
    subjects=frozenset({"other-tenant"}),
    classifications=frozenset({"internal"}),
)


def _chunks(
    fingerprint,
    text: str = "contenido de contrato",
    *,
    content_hash: str = "hash",
    target_tokens: int = 500,
) -> list[DocumentChunk]:
    candidate = DocumentCandidate(
        "demo", Path("doc.txt"), "doc.txt", "file:///doc.txt", content_hash
    )
    return chunk_document(
        candidate,
        [ExtractedUnit(text)],
        target_tokens=target_tokens,
        overlap_tokens=0,
        fingerprint=fingerprint,
    )


def _search(store, scope: Scope = SINGLE_TENANT_SCOPE, limit: int = 50):
    return store.search(VECTOR, limit=limit, score_threshold=None, scope=scope)


def test_backend_implements_the_publication_port(contract_store) -> None:
    assert isinstance(contract_store, IndexPublicationPort)


def test_chunks_round_trip_through_upsert_list_search_and_delete(
    contract_store, make_fingerprint
) -> None:
    fingerprint = make_fingerprint()
    chunk = _chunks(fingerprint)[0]
    contract_store.ensure_collection(3, fingerprint)

    contract_store.upsert([chunk], [VECTOR])

    documents = contract_store.list_documents({"demo"})
    assert documents[chunk.document_id].content_hash == "hash"
    assert contract_store.list_documents({"another-source"}) == {}
    hits = _search(contract_store)
    assert len(hits) == 1
    assert hits[0].chunk == chunk
    assert hits[0].score == pytest.approx(1.0, abs=1e-4)

    contract_store.delete_document(chunk.document_id)
    assert contract_store.list_documents({"demo"}) == {}
    assert _search(contract_store) == []


def test_reads_and_writes_without_a_bound_fingerprint_are_rejected(
    contract_store, make_fingerprint
) -> None:
    chunk = _chunks(make_fingerprint())[0]

    with pytest.raises(AppError):
        _search(contract_store)
    with pytest.raises(AppError):
        contract_store.upsert([chunk], [VECTOR])


def test_ensure_collection_rejects_reuse_with_another_fingerprint(
    contract_store, make_fingerprint
) -> None:
    contract_store.ensure_collection(3, make_fingerprint())

    with pytest.raises(AppError) as excinfo:
        contract_store.ensure_collection(3, make_fingerprint(chunk_tokens=600))

    assert excinfo.value.kind is ErrorKind.VALIDATION


def test_a_stale_bound_fingerprint_fails_explicitly_after_the_alias_moves(
    contract_store, make_fingerprint
) -> None:
    current = make_fingerprint()
    other = make_fingerprint(chunk_tokens=600)
    contract_store.ensure_collection(3, current)
    contract_store.candidate_store(other).ensure_collection(3, other)

    contract_store.publish_alias(contract_store.physical_name_for(other))

    with pytest.raises(AppError) as excinfo:
        _search(contract_store)
    assert excinfo.value.kind is ErrorKind.VALIDATION


def test_prune_document_keeps_only_the_given_chunks(contract_store, make_fingerprint) -> None:
    fingerprint = make_fingerprint()
    contract_store.ensure_collection(3, fingerprint)
    old = _chunks(fingerprint, "uno dos tres cuatro", content_hash="v1", target_tokens=2)
    new = _chunks(fingerprint, "uno dos tres cuatro", content_hash="v2", target_tokens=2)
    assert len(old) > 1
    contract_store.upsert(old, [VECTOR for _ in old])
    contract_store.upsert(new, [VECTOR for _ in new])

    contract_store.prune_document(new[0].document_id, {chunk.chunk_id for chunk in new})

    assert {hit.chunk.chunk_id for hit in _search(contract_store)} == {
        chunk.chunk_id for chunk in new
    }
    assert contract_store.list_documents({"demo"})[new[0].document_id].content_hash == "v2"

    contract_store.prune_document(new[0].document_id, set())
    assert contract_store.list_documents({"demo"}) == {}


def test_search_prefilters_by_tenant_subject_and_classification(
    contract_store, make_fingerprint
) -> None:
    fingerprint = make_fingerprint()
    contract_store.ensure_collection(3, fingerprint)
    contract_store.upsert(_chunks(fingerprint), [VECTOR])
    tenant = SINGLE_TENANT_SCOPE.tenant

    assert len(_search(contract_store)) == 1
    assert _search(contract_store, Scope(tenant="other-tenant")) == []
    assert _search(
        contract_store,
        Scope(
            tenant=tenant,
            subjects=frozenset({"someone-else"}),
            classifications=SINGLE_TENANT_SCOPE.classifications,
        ),
    ) == []
    assert _search(
        contract_store,
        Scope(
            tenant=tenant,
            subjects=SINGLE_TENANT_SCOPE.subjects,
            classifications=frozenset({"restricted"}),
        ),
    ) == []


def test_update_acl_changes_visibility_without_touching_vectors(
    contract_store, make_fingerprint
) -> None:
    fingerprint = make_fingerprint()
    chunk = _chunks(fingerprint)[0]
    contract_store.ensure_collection(3, fingerprint)
    contract_store.upsert([chunk], [VECTOR])
    score_before = _search(contract_store)[0].score

    contract_store.update_acl(chunk.document_id, OTHER_TENANT_ACL)

    assert _search(contract_store) == []
    hits = _search(contract_store, OTHER_TENANT_SCOPE)
    assert len(hits) == 1
    assert hits[0].chunk.tenant_id == "other-tenant"
    assert hits[0].chunk.text == chunk.text
    assert hits[0].score == pytest.approx(score_before, abs=1e-6)


def test_scan_chunks_returns_full_chunks_within_scope(contract_store, make_fingerprint) -> None:
    fingerprint = make_fingerprint()
    chunk = _chunks(fingerprint, "contenido lexico")[0]
    contract_store.ensure_collection(3, fingerprint)
    contract_store.upsert([chunk], [VECTOR])

    assert contract_store.scan_chunks(SINGLE_TENANT_SCOPE) == [chunk]
    assert contract_store.scan_chunks(OTHER_TENANT_SCOPE) == []


def test_publish_and_rollback_keep_the_previous_index_available(
    contract_store, make_fingerprint
) -> None:
    first = make_fingerprint()
    second = make_fingerprint(chunk_tokens=600)
    assert contract_store.published_physical_name() is None
    contract_store.ensure_collection(3, first)
    first_physical = contract_store.physical_name_for(first)
    second_physical = contract_store.physical_name_for(second)
    assert first_physical != second_physical
    assert contract_store.logical_name
    assert contract_store.published_physical_name() == first_physical
    contract_store.upsert(_chunks(first), [VECTOR])

    candidate = contract_store.candidate_store(second)
    candidate.ensure_collection(3, second)
    candidate.upsert(_chunks(second, "contenido candidato"), [VECTOR])
    # The candidate is invisible through the alias until published.
    assert contract_store.published_physical_name() == first_physical
    assert [hit.chunk.text for hit in _search(contract_store)] == ["contenido de contrato"]

    contract_store.publish_alias(second_physical)
    assert contract_store.published_physical_name() == second_physical
    contract_store.bind_fingerprint(second)
    assert [hit.chunk.text for hit in _search(contract_store)] == ["contenido candidato"]

    contract_store.rollback_alias(first_physical)
    assert contract_store.published_physical_name() == first_physical
    contract_store.bind_fingerprint(first)
    assert [hit.chunk.text for hit in _search(contract_store)] == ["contenido de contrato"]


def test_rollback_to_a_missing_index_fails_explicitly(contract_store, make_fingerprint) -> None:
    contract_store.ensure_collection(3, make_fingerprint())

    with pytest.raises(AppError) as excinfo:
        contract_store.rollback_alias(
            contract_store.physical_name_for(make_fingerprint(chunk_tokens=999))
        )

    assert excinfo.value.kind is ErrorKind.NOT_FOUND
