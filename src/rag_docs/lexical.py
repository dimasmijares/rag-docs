"""BM25 lexical retrieval and score fusion (``WRK-TASK-037``, ``RFC-001`` gate G2).

Pure Python, no new dependency: the scoring formula stays inline and
inspectable, which is what "explicable" means for the Acceptance Criteria of
this task, and avoids a supply-chain addition for a PoC-scale corpus. Built
on demand from the chunks a caller supplies rather than persisted, so it has
no ``IndexFingerprint`` of its own — it is derived deterministically from
text already covered by the fingerprinted vector index (``RULE-004``).
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

from rag_docs.contracts import DocumentChunk, SearchHit

# Standard Robertson/Sparck-Jones BM25 constants (Manning, Raghavan &
# Schutze, *Introduction to Information Retrieval*, ch. 11).
BM25_K1 = 1.5
BM25_B = 0.75
LEXICAL_VERSION = "bm25-v1"

# Reciprocal Rank Fusion constant from Cormack, Clarke & Buettcher, 2009
# ("Reciprocal Rank Fusion outperforms Condorcet and individual Rank
# Learning Methods"). Explicit and versioned so a future change is a new
# name, not a silent behavior shift (contracts compatibility policy).
RRF_K = 60
FUSION_VERSION = "rrf-v1"

# Underscore stays part of a token: technical identifiers like
# ETL_CLIENTES_DIARIA are exactly what exact-match lexical retrieval needs to
# find over a dense embedding that can blur them into nearby text (AC2).
_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


def tokenize(text: str) -> list[str]:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    unaccented = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return _TOKEN_PATTERN.findall(unaccented)


@dataclass(frozen=True, slots=True)
class LexicalHit:
    chunk: DocumentChunk
    score: float


class BM25Index:
    """BM25 over the chunks given at construction time.

    Rebuilt per query from a full scope-filtered scan (``VectorStore.
    scan_chunks``): appropriate for the corpus sizes this PoC targets, and it
    means a permission change or a content rewrite is reflected on the next
    query with nothing to invalidate, unlike a persisted secondary index.
    """

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self.chunks = chunks
        self._doc_tokens = [tokenize(chunk.text) for chunk in chunks]
        self._doc_lengths = [len(tokens) for tokens in self._doc_tokens]
        self._avg_doc_length = (
            sum(self._doc_lengths) / len(self._doc_lengths) if self._doc_lengths else 0.0
        )
        self._doc_frequency: dict[str, int] = {}
        for tokens in self._doc_tokens:
            for term in set(tokens):
                self._doc_frequency[term] = self._doc_frequency.get(term, 0) + 1

    def _idf(self, term: str) -> float:
        n = len(self.chunks)
        df = self._doc_frequency.get(term, 0)
        return math.log((n - df + 0.5) / (df + 0.5) + 1)

    def search(self, query: str, limit: int) -> list[LexicalHit]:
        query_terms = tokenize(query)
        scored: list[tuple[float, int]] = []
        for index, tokens in enumerate(self._doc_tokens):
            doc_length = self._doc_lengths[index]
            if not doc_length:
                continue
            term_counts: dict[str, int] = {}
            for term in tokens:
                term_counts[term] = term_counts.get(term, 0) + 1
            score = 0.0
            for term in query_terms:
                frequency = term_counts.get(term, 0)
                if frequency == 0:
                    continue
                idf = self._idf(term)
                numerator = frequency * (BM25_K1 + 1)
                denominator = frequency + BM25_K1 * (
                    1 - BM25_B + BM25_B * doc_length / (self._avg_doc_length or 1)
                )
                score += idf * numerator / denominator
            if score > 0:
                scored.append((score, index))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            LexicalHit(chunk=self.chunks[index], score=score)
            for score, index in scored[:limit]
        ]


def reciprocal_rank_fusion(
    dense: list[SearchHit], lexical: list[LexicalHit], *, limit: int
) -> list[SearchHit]:
    """Combine two rankings by rank alone (RRF), not by raw score: dense
    cosine similarity and BM25 live on incomparable scales, so fusing scores
    directly would silently let whichever retriever has the larger numbers
    dominate. The fused score is the explicit, inspectable sum of
    ``1 / (RRF_K + rank)`` across every ranking a chunk appears in.
    """
    fused_score: dict[str, float] = {}
    chunk_by_id: dict[str, DocumentChunk] = {}
    for rank, hit in enumerate(dense, start=1):
        chunk_id = hit.chunk.chunk_id
        fused_score[chunk_id] = fused_score.get(chunk_id, 0.0) + 1 / (RRF_K + rank)
        chunk_by_id.setdefault(chunk_id, hit.chunk)
    for rank, hit in enumerate(lexical, start=1):
        chunk_id = hit.chunk.chunk_id
        fused_score[chunk_id] = fused_score.get(chunk_id, 0.0) + 1 / (RRF_K + rank)
        chunk_by_id.setdefault(chunk_id, hit.chunk)
    ordered = sorted(fused_score.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [
        SearchHit(chunk=chunk_by_id[chunk_id], score=score) for chunk_id, score in ordered
    ]
