"""Live migration + rollback drill over the synthetic demo corpus (``WRK-TASK-091``,
``WRK-TASK-101``).

Reproducible end-to-end proof that ``migrate_and_publish``/``rollback_alias``
(``WRK-TASK-036``) work against real data, not only the fakes in
``tests/test_indexing.py``: builds the published index, migrates to a
deliberately different chunking (a new ``IndexFingerprint``), validates the
candidate with a real search before the alias moves, and then rolls back and
confirms the previous physical index still serves correct results.

``--backend qdrant`` (default) uses an in-memory Qdrant client and the local
embedding model — no Docker, no new infrastructure (``WRK-TASK-091`` AC5).
``--backend fabric_sql`` runs the same drill against SQL database in Fabric
through the ports only (``WRK-TASK-101``); connection and identity come from
``RAG_DOCS_FABRIC_*`` as set by ``scripts/verify-fabric.ps1``. The Fabric drill
starts from and leaves a clean logical index unless ``--keep`` is given.

Exits non-zero if any check fails.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from rag_docs.config import Settings, load_sources
from rag_docs.contracts import SINGLE_TENANT_SCOPE, AppError
from rag_docs.embeddings import SentenceTransformerEmbedder
from rag_docs.indexing import IndexingService, migrate_and_publish
from rag_docs.sources.local import LocalFolderSource
from rag_docs.vector_store import QdrantVectorStore

EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
EMBEDDING_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
PROBE_QUESTION = "proceso"
LOGICAL_NAME = "migration_drill"


def _embedder() -> SentenceTransformerEmbedder:
    return SentenceTransformerEmbedder(EMBEDDING_MODEL, 16, EMBEDDING_REVISION)


def _search(store: Any, embedder: SentenceTransformerEmbedder) -> list:
    vector = embedder.embed_query(PROBE_QUESTION)
    return store.search(vector, limit=5, score_threshold=None, scope=SINGLE_TENANT_SCOPE)


def _store(backend: str) -> Any:
    if backend == "qdrant":
        return QdrantVectorStore(":memory:", LOGICAL_NAME)
    from rag_docs.fabric_sql_store import build_fabric_sql_store

    store = build_fabric_sql_store(Settings(), LOGICAL_NAME)
    store.drop_logical_index()
    return store


def _physical_exists(store: Any, physical_name: str) -> bool:
    if isinstance(store, QdrantVectorStore):
        return store.client.collection_exists(physical_name)
    return store._physical_exists(physical_name)


def _emit(stage: dict[str, Any], checks: list[bool], *names: str) -> None:
    print(json.dumps(stage, indent=2))
    checks.extend(bool(stage[name]) for name in names)


def main() -> int:
    parser = argparse.ArgumentParser(description="Drill de migración y rollback")
    parser.add_argument("--backend", choices=["qdrant", "fabric_sql"], default="qdrant")
    parser.add_argument("--keep", action="store_true", help="No limpiar el índice Fabric al final")
    args = parser.parse_args()

    sources = [LocalFolderSource(item) for item in load_sources(Path("config/sources.yaml"))]
    store = _store(args.backend)
    checks: list[bool] = []

    live = IndexingService(sources, _embedder(), store, chunk_tokens=500, chunk_overlap=75)
    report = live.index()
    original_physical = store.published_physical_name()
    original_hits = _search(store, _embedder())
    _emit(
        {
            "stage": "initial-index",
            "backend": args.backend,
            "physical": original_physical,
            "fingerprint": live.fingerprint.digest(),
            "documents_added": report.added,
            "no_errors": not report.errors,
            "probe_hits": len(original_hits),
        },
        checks,
        "no_errors",
        "probe_hits",
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
    # serve the new index, until this process opts in.
    try:
        _search(store, _embedder())
        stale_binding_rejected = False
    except AppError:
        stale_binding_rejected = True
    store.bind_fingerprint(migrated.fingerprint)
    _emit(
        {
            "stage": "migrated",
            "physical": new_physical,
            "fingerprint": migrated.fingerprint.digest(),
            "alias_resolves_to_new": store.published_physical_name() == new_physical,
            "previous_still_exists": _physical_exists(store, original_physical),
            "stale_fingerprint_binding_rejected_search": stale_binding_rejected,
            "probe_hits_after_rebinding": len(_search(store, _embedder())),
        },
        checks,
        "alias_resolves_to_new",
        "previous_still_exists",
        "stale_fingerprint_binding_rejected_search",
        "probe_hits_after_rebinding",
    )

    store.rollback_alias(original_physical)
    store.bind_fingerprint(live.fingerprint)
    _emit(
        {
            "stage": "rolled-back",
            "alias_resolves_to_original": store.published_physical_name() == original_physical,
            "new_physical_still_exists_for_forensics": _physical_exists(store, new_physical),
            "probe_hits": len(_search(store, _embedder())),
        },
        checks,
        "alias_resolves_to_original",
        "new_physical_still_exists_for_forensics",
        "probe_hits",
    )

    if args.backend == "fabric_sql" and not args.keep:
        store.drop_logical_index()
    return 0 if all(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
