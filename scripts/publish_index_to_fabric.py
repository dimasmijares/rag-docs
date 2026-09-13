"""Publish the locally built index to SQL database in Fabric (``WRK-TASK-101``).

Walking skeleton of the Fabric profile: the index is built on this machine with the pinned
embedder (the same ``IndexFingerprint`` as the local app, ``WRK-TASK-095``), copied chunk by
chunk with its vectors into a Fabric SQL candidate bound to that fingerprint, validated, and only
then published through the alias (``RULE-004``). Nothing is re-embedded on the Fabric side, so the
published digest is the local digest by construction and is checked explicitly.

The local build uses the embedded Qdrant client (``:memory:``) unless ``--source-qdrant-url``
points at a running Qdrant whose alias already serves the same fingerprint.

Connection and identity come from ``Settings`` (``RAG_DOCS_FABRIC_*``), as set by
``scripts/verify-fabric.ps1``. Output is JSON without server, database or identity values.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rag_docs.config import Settings, load_sources
from rag_docs.container import build_embedder
from rag_docs.contracts import SINGLE_TENANT_SCOPE, chunk_from_payload
from rag_docs.fabric_sql_store import build_fabric_sql_store
from rag_docs.indexing import IndexingService
from rag_docs.sources.local import LocalFolderSource
from rag_docs.vector_store import QdrantVectorStore

PROBE_QUESTION = "¿Qué ETL carga la tabla maestra de clientes?"
BATCH_SIZE = 64


def _local_points(store: QdrantVectorStore) -> list[tuple[object, list[float]]]:
    physical = store.published_physical_name()
    points: list[tuple[object, list[float]]] = []
    offset = None
    while True:
        batch, offset = store.client.scroll(
            collection_name=physical,
            limit=256,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        points.extend(
            (chunk_from_payload(point.payload or {}), list(point.vector)) for point in batch
        )
        if offset is None:
            return points


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sources", type=Path, default=Path("config/sources.yaml"))
    parser.add_argument("--source-qdrant-url", default=":memory:")
    args = parser.parse_args()

    settings = Settings()
    embedder = build_embedder(settings)
    local_store = QdrantVectorStore(args.source_qdrant_url, settings.qdrant_collection)
    sources = [LocalFolderSource(item) for item in load_sources(args.sources)]
    local = IndexingService(
        sources, embedder, local_store, settings.chunk_tokens, settings.chunk_overlap
    )
    if args.source_qdrant_url == ":memory:":
        report = local.index()
        if report.errors:
            raise SystemExit(f"La indexación local falló: {len(report.errors)} error(es).")
    else:
        local_store.bind_fingerprint(local.fingerprint)
        local_store.verify_fingerprint(local.fingerprint)
    fingerprint = local.fingerprint
    points = _local_points(local_store)

    target = build_fabric_sql_store(settings)
    candidate = target.candidate_store(fingerprint)
    candidate.ensure_collection(fingerprint.dimension, fingerprint)
    for start in range(0, len(points), BATCH_SIZE):
        batch = points[start : start + BATCH_SIZE]
        candidate.upsert([chunk for chunk, _ in batch], [vector for _, vector in batch])

    probe = embedder.embed_query(PROBE_QUESTION)
    local_hits = local_store.search(probe, 5, None, SINGLE_TENANT_SCOPE)
    candidate_hits = candidate.search(probe, 5, None, SINGLE_TENANT_SCOPE)
    candidate_chunks = candidate.scan_chunks(SINGLE_TENANT_SCOPE)
    checks = {
        "same_chunk_count": len(candidate_chunks) == len(points),
        "same_chunk_ids": {chunk.chunk_id for chunk in candidate_chunks}
        == {chunk.chunk_id for chunk, _ in points},
        "same_top_hits": [hit.chunk.chunk_id for hit in candidate_hits]
        == [hit.chunk.chunk_id for hit in local_hits],
        "top_score_delta_below_1e-4": bool(local_hits and candidate_hits)
        and abs(local_hits[0].score - candidate_hits[0].score) < 1e-4,
    }
    physical = target.physical_name_for(fingerprint)
    published = all(checks.values())
    if published:
        target.publish_alias(physical)
        target.bind_fingerprint(fingerprint)
        target.verify_fingerprint(fingerprint)
    result = {
        "local_fingerprint_digest": fingerprint.digest(),
        "local_chunks": len(points),
        "validation": checks,
        "published": published,
        "published_physical": target.published_physical_name(),
        "published_digest_matches_local": target.published_physical_name()
        == f"{target.logical_name}__{fingerprint.digest()}",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    target.close()
    candidate.close()
    return 0 if published and result["published_digest_matches_local"] else 1


if __name__ == "__main__":
    sys.exit(main())
