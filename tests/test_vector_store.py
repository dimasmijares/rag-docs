from pathlib import Path

from qdrant_client import QdrantClient

from rag_docs.chunking import chunk_document
from rag_docs.models import DocumentCandidate, ExtractedUnit
from rag_docs.vector_store import QdrantVectorStore


def test_qdrant_adapter_with_in_memory_client(tmp_path: Path) -> None:
    path = tmp_path / "doc.txt"
    path.write_text("documentación técnica", encoding="utf-8")
    candidate = DocumentCandidate("demo", path, "doc.txt", path.as_uri(), "hash")
    chunk = chunk_document(candidate, [ExtractedUnit("documentación técnica")])[0]
    store = QdrantVectorStore.__new__(QdrantVectorStore)
    store.client = QdrantClient(":memory:")
    store.collection_name = "test"

    store.ensure_collection(3)
    store.upsert([chunk], [[1.0, 0.0, 0.0]])

    documents = store.list_documents({"demo"})
    hits = store.search([1.0, 0.0, 0.0], limit=8, score_threshold=0.1)
    store.delete_document(candidate.document_id)

    assert candidate.document_id in documents
    assert hits[0].chunk.relative_path == "doc.txt"
    assert hits[0].score > 0.9
    assert store.list_documents({"demo"}) == {}
