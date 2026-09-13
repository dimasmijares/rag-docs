"""DiskANN experiment on SQL database in Fabric (``WRK-TASK-102``, gate G2 of ``RFC-001``).

Measures whether an approximate DiskANN vector index (preview) could replace the exact
``VECTOR_DISTANCE`` search of ``FabricSqlVectorStore`` without breaking ``RULE-003`` or losing
recall. It never touches the published index: it copies its chunks into a temporary table with the
integer clustered key a vector index requires, adds near-duplicate distractors that belong to a
different tenant (the case a post-filtered approximate search gets wrong), and compares for every
gold-set question:

- ``exact``: ``TOP k`` over ``VECTOR_DISTANCE`` with the scope prefilter in ``WHERE``.
- ``diskann``: ``SELECT TOP k ... FROM VECTOR_SEARCH(...)`` with the scope filter in ``WHERE``.
  Newer DiskANN index versions reject an explicit ``TOP_N`` and filter iteratively, so the
  experiment measures whether that still returns ``k`` in-scope results.

Output: metrics only (case ids, overlaps, document recall, latencies within this backend), never
chunk text. The temporary table is dropped at the end. Connection comes from ``RAG_DOCS_FABRIC_*``.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path
from statistics import mean, median
from typing import Any

import yaml

from rag_docs.config import Settings
from rag_docs.container import build_embedder
from rag_docs.contracts import SINGLE_TENANT_SCOPE, AppError, ErrorKind
from rag_docs.fabric_sql_store import build_fabric_sql_store
from rag_docs.indexing import build_fingerprint

TABLE = "dbo.diskann_experiment"
INDEX = "vix_diskann_experiment"
TOP_K = 8
DISTRACTORS_PER_CHUNK = 14
NOISE = 0.05
FILLER_TENANT = "diskann-filler"
GOLD_SETS = ("evaluation/gold-set.dev.yaml", "evaluation/gold-set.validation.yaml")


def _normalize(vector: list[float]) -> list[float]:
    norm = sum(value * value for value in vector) ** 0.5 or 1.0
    return [value / norm for value in vector]


def _cause(exc: AppError) -> str:
    """SQL server message behind a mapped ``AppError``, without endpoint or driver prefixes."""
    text = str(exc.__cause__ or exc.message)
    text = re.sub(
        r"(?i)[a-z0-9-]+\.(database|datawarehouse)\.fabric\.microsoft\.com", "<sql>", text
    )
    return text.rsplit("]", 1)[-1].strip()[:300]


def _timed(cursor: Any, sql: str, parameters: tuple) -> tuple[list[tuple], float]:
    started = time.perf_counter()
    cursor.execute(sql, parameters)
    rows = cursor.fetchall()
    return rows, (time.perf_counter() - started) * 1000


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--build-timeout", type=int, default=900)
    args = parser.parse_args()

    settings = Settings()
    embedder = build_embedder(settings)
    fingerprint = build_fingerprint(embedder, settings.chunk_tokens, settings.chunk_overlap)
    store = build_fabric_sql_store(settings)
    store.bind_fingerprint(fingerprint)
    physical = store.verify_fingerprint(fingerprint)
    chunks_table = f"dbo.[{physical}__chunks]"
    dimension = fingerprint.dimension
    rng = random.Random(0)
    result: dict[str, Any] = {
        "experiment": "wrk-task-102-diskann",
        "index_fingerprint": fingerprint.digest(),
        "vector_backend": "fabric_sql",
        "top_k": TOP_K,
        "distractors_per_chunk": DISTRACTORS_PER_CHUNK,
        "distractor_noise": NOISE,
    }

    with store._cursor() as cursor:
        cursor.execute(
            f"SELECT chunk_id, tenant_id, classification, payload, "
            f"CAST(embedding AS NVARCHAR(MAX)) FROM {chunks_table}"
        )
        source_rows = cursor.fetchall()
    documents = {
        str(chunk_id): json.loads(payload)["relative_path"]
        for chunk_id, _, _, payload, _ in source_rows
    }
    rows: list[tuple] = []
    for chunk_id, tenant, classification, _, embedding in source_rows:
        vector = json.loads(embedding)
        rows.append((str(chunk_id), tenant, classification, json.dumps(vector)))
        for copy in range(DISTRACTORS_PER_CHUNK):
            noisy = _normalize([value + rng.gauss(0.0, NOISE) for value in vector])
            rows.append(
                (f"filler-{chunk_id[:12]}-{copy}", FILLER_TENANT, classification, json.dumps(noisy))
            )
    result["rows"] = {"in_scope": len(source_rows), "distractors": len(rows) - len(source_rows)}

    with store._cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE}")
        cursor.execute(
            f"CREATE TABLE {TABLE} (id INT IDENTITY(1, 1) NOT NULL PRIMARY KEY CLUSTERED, "
            "chunk_id VARCHAR(64) NOT NULL, tenant_id NVARCHAR(128) NOT NULL, "
            f"classification NVARCHAR(64) NOT NULL, embedding VECTOR({dimension}) NOT NULL)"
        )
        cursor.executemany(
            f"INSERT INTO {TABLE} (chunk_id, tenant_id, classification, embedding) "
            f"VALUES (?, ?, ?, CAST(? AS VECTOR({dimension})))",
            rows,
        )

    cases = []
    for gold_path in GOLD_SETS:
        gold = yaml.safe_load(Path(gold_path).read_text(encoding="utf-8"))
        for case in gold["cases"]:
            if case.get("expected_status") == "grounded":
                cases.append((gold["split"], case))

    exact_sql = (
        f"DECLARE @q VECTOR({dimension}) = CAST(? AS VECTOR({dimension})); "
        f"SELECT TOP ({TOP_K}) chunk_id FROM {TABLE} "
        "WHERE tenant_id = ? AND classification = ? "
        "ORDER BY VECTOR_DISTANCE('cosine', embedding, @q), chunk_id"
    )

    diskann_sql = (
        f"DECLARE @q VECTOR({dimension}) = CAST(? AS VECTOR({dimension})); "
        f"SELECT TOP ({TOP_K}) WITH APPROXIMATE t.chunk_id "
        f"FROM VECTOR_SEARCH(TABLE = {TABLE} AS t, "
        "COLUMN = embedding, SIMILAR_TO = @q, METRIC = 'cosine') AS s "
        "WHERE t.tenant_id = ? AND t.classification = ? ORDER BY s.distance"
    )

    classification = next(iter(SINGLE_TENANT_SCOPE.classifications))
    tenant = SINGLE_TENANT_SCOPE.tenant
    queries = {case["id"]: _normalize(embedder.embed_query(case["question"])) for _, case in cases}

    # Baseline before the index exists: the vector index may make the table read-only.
    exact: dict[str, list[str]] = {}
    exact_latency: list[float] = []
    store_parity: list[bool] = []
    with store._cursor() as cursor:
        for _, case in cases:
            params = (json.dumps(queries[case["id"]]), tenant, classification)
            rows_out, elapsed = _timed(cursor, exact_sql, params)
            exact[case["id"]] = [str(row[0]) for row in rows_out]
            exact_latency.append(elapsed)
    for _, case in cases:
        hits = store.search(queries[case["id"]], TOP_K, None, SINGLE_TENANT_SCOPE)
        store_parity.append([hit.chunk.chunk_id for hit in hits] == exact[case["id"]])

    started = time.perf_counter()
    build_error = None
    # CREATE VECTOR INDEX cannot run inside a user transaction: use an autocommit connection.
    connection = store._connect()
    try:
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(
            f"CREATE VECTOR INDEX {INDEX} ON {TABLE}(embedding) "
            "WITH (METRIC = 'cosine', TYPE = 'diskann')"
        )
    except Exception as exc:
        build_error = _cause(AppError(ErrorKind.DEPENDENCY_UNAVAILABLE, str(exc)))
    finally:
        connection.close()
    usable = False
    last_error = build_error
    while build_error is None and time.perf_counter() - started < args.build_timeout:
        try:
            with store._cursor() as cursor:
                _timed(
                    cursor,
                    diskann_sql,
                    (json.dumps(queries[cases[0][1]["id"]]), tenant, classification),
                )
            usable = True
            break
        except AppError as exc:
            last_error = _cause(exc)
            if "being built" not in last_error:
                break
            time.sleep(15)
    result["diskann_index"] = {
        "usable": usable,
        "seconds_until_usable": round(time.perf_counter() - started, 1) if usable else None,
        "last_error": None if usable else last_error,
    }

    per_case = []
    variants = {"diskann": diskann_sql}
    latencies: dict[str, list[float]] = {name: [] for name in variants}
    if usable:
        with store._cursor() as cursor:
            for split, case in cases:
                params = (json.dumps(queries[case["id"]]), tenant, classification)
                entry: dict[str, Any] = {"split": split, "case_id": case["id"]}
                expected = set(case.get("expected_documents") or [])
                for name, sql in {"exact": None, **variants}.items():
                    if name == "exact":
                        ids = exact[case["id"]]
                    else:
                        found, elapsed = _timed(cursor, sql, params)
                        ids = [str(row[0]) for row in found]
                        latencies[name].append(elapsed)
                    docs = {documents[chunk_id] for chunk_id in ids if chunk_id in documents}
                    entry[name] = {
                        "returned": len(ids),
                        "overlap_with_exact": len(set(ids) & set(exact[case["id"]])),
                        "document_recall": (len(expected & docs) / len(expected))
                        if expected
                        else None,
                    }
                per_case.append(entry)

    def summary(name: str) -> dict[str, Any]:
        values = [entry[name] for entry in per_case]
        recalls = [
            item["document_recall"] for item in values if item["document_recall"] is not None
        ]
        return {
            "mean_returned": round(mean(item["returned"] for item in values), 3),
            "cases_with_fewer_than_k": sum(item["returned"] < TOP_K for item in values),
            "mean_overlap_with_exact": round(
                mean(item["overlap_with_exact"] for item in values), 3
            ),
            "mean_document_recall": round(mean(recalls), 6) if recalls else None,
        }

    result["exact_matches_fabric_sql_store"] = all(store_parity)
    if per_case:
        result["summary"] = {name: summary(name) for name in ("exact", *variants)}
        result["latency_ms_p50_same_backend"] = {
            "exact": round(median(exact_latency), 2),
            **{name: round(median(values), 2) for name, values in latencies.items()},
        }
        best = result["summary"]["diskann"]
        exact_summary = result["summary"]["exact"]
        improves = (
            best["mean_document_recall"] is not None
            and best["mean_document_recall"] > exact_summary["mean_document_recall"]
        )
        result["decision"] = {
            "adopted": improves,
            "reason": "DiskANN no mejora el recall de la búsqueda exacta"
            if not improves
            else "DiskANN mejora el recall medido",
        }
    else:
        result["decision"] = {"adopted": False, "reason": "índice DiskANN no utilizable"}
    result["cases"] = per_case

    with store._cursor() as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE}")
    store.close()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: result[key] for key in result if key != "cases"}, indent=2, ensure_ascii=False
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
