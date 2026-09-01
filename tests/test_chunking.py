from pathlib import Path

from rag_docs.chunking import chunk_document
from rag_docs.models import DocumentCandidate, ExtractedUnit


def test_chunking_preserves_metadata_and_overlap(tmp_path: Path) -> None:
    path = tmp_path / "doc.md"
    path.write_text("x", encoding="utf-8")
    document = DocumentCandidate("demo", path, "doc.md", path.as_uri(), "hash")
    unit = ExtractedUnit(
        text=" ".join(f"word-{index}" for index in range(12)),
        locator={"page": 2},
        section="Detalles",
    )

    chunks = chunk_document(document, [unit], target_tokens=5, overlap_tokens=2)

    assert len(chunks) == 4
    assert chunks[0].locator == {"page": 2}
    assert chunks[0].section == "Detalles"
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)
