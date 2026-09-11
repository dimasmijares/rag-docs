from pathlib import Path

from rag_docs.chunking import chunk_document
from rag_docs.contracts import SearchHit
from rag_docs.lexical import BM25Index, reciprocal_rank_fusion, tokenize
from rag_docs.models import DocumentCandidate, ExtractedUnit


def make_chunk(tmp_path: Path, text: str, relative_path: str = "doc.md"):
    path = tmp_path / Path(relative_path).name
    path.write_text(text, encoding="utf-8")
    candidate = DocumentCandidate("demo", path, relative_path, path.as_uri(), "hash")
    return chunk_document(candidate, [ExtractedUnit(text)])[0]


def test_tokenize_folds_case_and_accents() -> None:
    assert tokenize("Consulta técnica ETL_CLIENTES") == ["consulta", "tecnica", "etl_clientes"]


def test_bm25_ranks_exact_lexical_match_above_unrelated_text(tmp_path: Path) -> None:
    exact = make_chunk(tmp_path, "El identificador ETL_CLIENTES_DIARIA carga clientes.", "a.md")
    unrelated = make_chunk(tmp_path, "La política de vacaciones se revisa cada año.", "b.md")
    index = BM25Index([exact, unrelated])

    hits = index.search("ETL_CLIENTES_DIARIA", limit=8)

    assert hits[0].chunk.chunk_id == exact.chunk_id
    assert len(hits) == 1


def test_bm25_returns_nothing_for_a_query_with_no_overlap(tmp_path: Path) -> None:
    chunk = make_chunk(tmp_path, "Contenido totalmente distinto.", "a.md")
    index = BM25Index([chunk])

    assert index.search("xilofono marciano inexistente", limit=8) == []


def test_bm25_handles_an_empty_corpus() -> None:
    index = BM25Index([])

    assert index.search("cualquier cosa", limit=8) == []


def test_reciprocal_rank_fusion_boosts_chunks_present_in_both_rankings(tmp_path: Path) -> None:
    shared = make_chunk(tmp_path, "compartido", "a.md")
    dense_only = make_chunk(tmp_path, "solo denso", "b.md")
    lexical_only = make_chunk(tmp_path, "solo lexico", "c.md")
    dense = [SearchHit(shared, 0.9), SearchHit(dense_only, 0.8)]
    lexical_index = BM25Index([shared, lexical_only])
    lexical_hits = [hit for hit in lexical_index.search("compartido lexico", limit=8)]

    fused = reciprocal_rank_fusion(dense, lexical_hits, limit=8)

    assert fused[0].chunk.chunk_id == shared.chunk_id
    fused_ids = {hit.chunk.chunk_id for hit in fused}
    assert dense_only.chunk_id in fused_ids
    assert lexical_only.chunk_id in fused_ids


def test_reciprocal_rank_fusion_respects_the_limit(tmp_path: Path) -> None:
    chunks = [make_chunk(tmp_path, f"documento numero {i}", f"doc{i}.md") for i in range(5)]
    dense = [SearchHit(chunk, 1.0 - index * 0.01) for index, chunk in enumerate(chunks)]

    fused = reciprocal_rank_fusion(dense, [], limit=2)

    assert len(fused) == 2
