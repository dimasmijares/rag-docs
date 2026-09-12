"""Live migration + rollback drill over the synthetic demo corpus (``WRK-TASK-091``).

Reproducible end-to-end proof that ``migrate_and_publish``/``rollback_alias``
(``WRK-TASK-036``) work against real data, not only the fakes in
``tests/test_indexing.py``: builds the published collection, migrates to a
deliberately different chunking (a new ``IndexFingerprint``), validates the
candidate with a real search before the alias moves, and then rolls back and
confirms the previous physical collection still serves correct results.

Uses an in-memory Qdrant client and the local embedding model already
required by ``v0.2.0`` — no Docker, no new infrastructure (``WRK-TASK-091``
AC5).
"""

from __future__ import annotations

import json
from pathlib import Path

from rag_docs.config import load_sources
from rag_docs.contracts import SINGLE_TENANT_SCOPE, AppError
from rag_docs.embeddings import SentenceTransformerEmbedder
from rag_docs.indexing import IndexingService, migrate_and_publish
from rag_docs.sources.local import LocalFolderSource
from rag_docs.vector_store import QdrantVectorStore

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
PROBE_QUESTION = "proceso"


def _embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(EMBEDDING_MODEL, 16, EMBEDDING_REVISION)


def _search(store: QdrantVectorStore, embedder: SentenceTransformerEmbedder) -> list:
    vector = embedder.embed_query(PROBE_QUESTION)
    return store.search(vector, limit=5, score_threshold=None, scope=SINGLE_TENANT_SCOPE)


def main() -> None:
    sources = [LocalFolderSource(item) for item in load_sources(Path("config/sources.yaml"))]
    store = QdrantVectorStore(":memory:", "migration-drill")

    live = IndexingService(sources, _embedder(), store, chunk_tokens=500, chunk_overlap=75)
    report = live.index()
    original_physical = store._resolve_alias()
    original_hits = _search(store, _embedder())
    print(
        json.dumps(
            {
                "stage": "initial-index",
                "physical": original_physical,
                "fingerprint": live.fingerprint.digest(),
                "documents_added": report.added,
                "errors": len(report.errors),
                "probe_hits": len(original_hits),
            },
            indent=2,
        )
    )

    migrated = IndexingService(sources, _embedder(), store, chunk_tokens=300, chunk_overlap=50)

    def validate(candidate_report, candidate_store) -> bool:
        if candidate_report.errors:
            return False
        return len(_search(candidate_store, _embedder())) > 0

    new_physical = migrate_and_publish(migrated, validate)
    # migrate_and_publish moves the alias but never rebinds a caller's own
    # store: RULE-004 keeps ``store`` bound to the fingerprint it started
    # with, so any search through it must fail explicitly, not silently
    # serve the new collection, until this process opts in.
    try:
        _search(store, _embedder())
        stale_binding_rejected = False
    except AppError:
        stale_binding_rejected = True
    store.bind_fingerprint(migrated.fingerprint)
    print(
        json.dumps(
            {
                "stage": "migrated",
                "physical": new_physical,
                "fingerprint": migrated.fingerprint.digest(),
                "alias_resolves_to_new": store._resolve_alias() == new_physical,
                "previous_still_exists": store.client.collection_exists(original_physical),
                "stale_fingerprint_binding_rejected_search": stale_binding_rejected,
                "probe_hits_after_rebinding": len(_search(store, _embedder())),
            },
            indent=2,
        )
    )

    store.rollback_alias(original_physical)
    store.bind_fingerprint(live.fingerprint)
    print(
        json.dumps(
            {
                "stage": "rolled-back",
                "alias_resolves_to_original": store._resolve_alias() == original_physical,
                "new_physical_still_exists_for_forensics": store.client.collection_exists(
                    new_physical
                ),
                "probe_hits": len(_search(store, _embedder())),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
