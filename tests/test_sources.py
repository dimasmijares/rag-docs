from pathlib import Path

from rag_docs.config import SourceDefinition, load_sources
from rag_docs.sources.local import LocalFolderSource


def test_source_config_resolves_relative_root(tmp_path: Path) -> None:
    documents = tmp_path / "docs"
    documents.mkdir()
    config = tmp_path / "sources.yaml"
    config.write_text(
        "sources:\n  - id: local\n    type: local_folder\n    root: docs\n",
        encoding="utf-8",
    )
    source = load_sources(config)[0]
    assert source.root == documents.resolve()


def test_local_source_discovers_recursively_and_excludes(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    expected = tmp_path / "nested" / "guide.md"
    expected.write_text("contenido", encoding="utf-8")
    (tmp_path / "~$draft.docx").write_bytes(b"ignored")
    (tmp_path / "image.png").write_bytes(b"ignored")
    definition = SourceDefinition(id="local", root=tmp_path)

    candidates = LocalFolderSource(definition).discover()

    assert [candidate.relative_path for candidate in candidates] == ["nested/guide.md"]
    assert candidates[0].original_uri.startswith("file:")
    assert len(candidates[0].content_hash) == 64
