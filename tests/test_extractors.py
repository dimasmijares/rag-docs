from pathlib import Path

import pytest

from rag_docs.extractors import ExtractionError, extract_document
from rag_docs.models import DocumentCandidate

ROOT = Path(__file__).parents[1] / "examples" / "corpus" / "demo"


def candidate(path: Path) -> DocumentCandidate:
    return DocumentCandidate("demo", path, path.relative_to(ROOT).as_posix(), path.as_uri(), "hash")


@pytest.mark.parametrize(
    ("relative", "locator"),
    [
        ("etl/catalogo-etl.md", None),
        ("operations/incidencias.txt", None),
        ("components/orquestador.docx", None),
        ("architecture/flujo-datos.pptx", "slide"),
        ("inventory/inventario-procesos.xlsx", "sheet"),
        ("runbooks/recuperacion-clientes.pdf", "page"),
    ],
)
def test_supported_extractors_return_text_and_locator(
    relative: str, locator: str | None
) -> None:
    units = extract_document(candidate(ROOT / relative))
    assert units
    assert any(unit.text.strip() for unit in units)
    if locator:
        assert locator in units[0].locator


def test_corrupt_document_is_isolated(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"not-a-pdf")
    broken = DocumentCandidate("demo", path, "broken.pdf", path.as_uri(), "hash")
    with pytest.raises(ExtractionError, match="broken.pdf"):
        extract_document(broken)
