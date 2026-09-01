from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from rag_docs.extractors import extract_document
from rag_docs.models import DocumentCandidate
from scripts.generate_demo_corpus import CORPUS_VERSION, FIXTURE_PATHS, SCHEMA_VERSION

ROOT = Path(__file__).parents[1]
CORPUS_ROOT = ROOT / "examples" / "corpus" / "demo"
EVALUATION_ROOT = ROOT / "evaluation"
DATASETS = {
    "dev": EVALUATION_ROOT / "gold-set.dev.yaml",
    "validation": EVALUATION_ROOT / "gold-set.validation.yaml",
}
FORMATS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md"}
ROOT_FIELDS = {"schema_version", "corpus_version", "split", "cases"}
CASE_REQUIRED_FIELDS = {
    "id",
    "category",
    "question",
    "expected_status",
    "expected_language",
    "target_fact_ids",
    "required_facts",
    "expected_documents",
    "expected_any_documents",
    "expected_locators",
}
CASE_OPTIONAL_FIELDS = {"equivalence_group", "reference_answer"}


def _load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _normalize_question(question: str) -> str:
    normalized = unicodedata.normalize("NFKC", question).casefold()
    return " ".join(re.sub(r"[^\w]+", " ", normalized).split())


def _all_documents(case: dict[str, Any]) -> set[str]:
    return {
        *case["expected_documents"],
        *case["expected_any_documents"],
        *(entry["document"] for entry in case["expected_locators"]),
    }


def _units(relative_path: str):
    path = CORPUS_ROOT / relative_path
    candidate = DocumentCandidate(
        "demo", path, relative_path, path.as_uri(), "synthetic-fixture"
    )
    return extract_document(candidate)


def test_gold_sets_follow_schema_and_minimum_coverage() -> None:
    minimums = {
        "dev": {"total": 16, "single_hop": 4, "compound": 3, "negative": 2, "other": 2},
        "validation": {
            "total": 8,
            "single_hop": 2,
            "compound": 2,
            "negative": 2,
            "other": 1,
        },
    }
    allowed_paths = set(FIXTURE_PATHS)

    for split, path in DATASETS.items():
        dataset = _load(path)
        assert set(dataset) == ROOT_FIELDS
        assert dataset["schema_version"] == SCHEMA_VERSION
        assert dataset["corpus_version"] == CORPUS_VERSION
        assert dataset["split"] == split
        cases = dataset["cases"]
        assert len(cases) >= minimums[split]["total"]
        assert len({case["id"] for case in cases}) == len(cases)
        assert len({_normalize_question(case["question"]) for case in cases}) == len(cases)

        categories = Counter(case["category"] for case in cases)
        for category in ("single_hop", "compound", "negative"):
            assert categories[category] >= minimums[split][category]
        assert sum(case["expected_language"] != "es" for case in cases) >= minimums[split][
            "other"
        ]

        referenced_formats: set[str] = set()
        for case in cases:
            assert CASE_REQUIRED_FIELDS <= set(case) <= CASE_REQUIRED_FIELDS | CASE_OPTIONAL_FIELDS
            assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case["id"])
            assert case["category"] in {"single_hop", "compound", "negative"}
            assert case["expected_language"] in {"es", "en"}
            documents = _all_documents(case)
            assert documents <= allowed_paths
            assert all("\\" not in item and ".." not in Path(item).parts for item in documents)
            referenced_formats.update(Path(item).suffix.casefold() for item in documents)

            if case["category"] == "negative":
                assert case["expected_status"] == "insufficient_evidence"
                assert not case["target_fact_ids"]
                assert not case["required_facts"]
                assert not documents
                assert "equivalence_group" not in case
            else:
                assert case["expected_status"] == "grounded"
                assert case["target_fact_ids"]
                assert case["required_facts"]
                assert case["expected_documents"] or case["expected_any_documents"]
                assert case["expected_locators"]
            if "equivalence_group" in case:
                assert len(case["expected_any_documents"]) >= 2

        assert referenced_formats == FORMATS


def test_splits_are_isolated() -> None:
    dev = _load(DATASETS["dev"])["cases"]
    validation = _load(DATASETS["validation"])["cases"]

    def values(cases: list[dict[str, Any]], field: str) -> set[str]:
        if field == "question":
            return {_normalize_question(case[field]) for case in cases}
        if field == "target_fact_ids":
            return {value for case in cases for value in case[field]}
        return {case[field] for case in cases if field in case}

    for field in ("id", "question", "target_fact_ids", "equivalence_group"):
        assert values(dev, field).isdisjoint(values(validation, field))


def test_expected_locators_exist_in_extracted_corpus() -> None:
    for path in DATASETS.values():
        for case in _load(path)["cases"]:
            for expected in case["expected_locators"]:
                units = _units(expected["document"])
                assert any(
                    ("section" not in expected or unit.section == expected["section"])
                    and ("locator" not in expected or unit.locator == expected["locator"])
                    for unit in units
                ), expected


def test_legacy_smoke_set_remains_compatible() -> None:
    smoke = _load(EVALUATION_ROOT / "gold-set.yaml")
    assert [case["id"] for case in smoke["cases"]] == [
        "etl-clientes",
        "ruta-etl-clientes",
        "incidencia-clientes",
        "fuera-de-corpus",
    ]
    assert all(
        {"id", "question", "expected_status", "expected_documents"} <= set(case)
        for case in smoke["cases"]
    )
