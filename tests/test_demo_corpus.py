from __future__ import annotations

import hashlib
import re
from pathlib import Path

from scripts.generate_demo_corpus import (
    CORPUS_VERSION,
    FIXTURE_PATHS,
    MANIFEST_NAME,
    SCHEMA_VERSION,
    check_corpus,
    generate_corpus,
)

ROOT = Path(__file__).parents[1]
CORPUS_ROOT = ROOT / "examples" / "corpus" / "demo"


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _manifest_entries(root: Path) -> list[tuple[str, str]]:
    lines = (root / MANIFEST_NAME).read_text(encoding="utf-8").splitlines()
    assert lines[:2] == [
        f"# corpus_version: {CORPUS_VERSION}",
        f"# schema_version: {SCHEMA_VERSION}",
    ]
    entries: list[tuple[str, str]] = []
    for line in lines[2:]:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\\]+)", line)
        assert match, line
        entries.append((match.group(1), match.group(2)))
    return entries


def test_manifest_is_sorted_complete_and_matches_fixture_bytes() -> None:
    entries = _manifest_entries(CORPUS_ROOT)
    paths = [path for _, path in entries]

    assert paths == sorted(FIXTURE_PATHS)
    assert len(paths) == len(set(paths))
    assert MANIFEST_NAME not in paths
    for digest, relative_path in entries:
        assert hashlib.sha256((CORPUS_ROOT / relative_path).read_bytes()).hexdigest() == digest


def test_generation_is_byte_deterministic_in_independent_directories(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    generate_corpus(first)
    generate_corpus(second)

    assert _tree(first) == _tree(second)


def test_canonical_corpus_matches_fresh_generation() -> None:
    assert set(_tree(CORPUS_ROOT)) == {*FIXTURE_PATHS, MANIFEST_NAME}
    check_corpus(CORPUS_ROOT)
