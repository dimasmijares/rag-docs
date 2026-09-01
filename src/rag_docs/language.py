from __future__ import annotations

import re
import unicodedata
from typing import Literal

SupportedLanguage = Literal["es", "en"]

_SPANISH_MARKERS = {
    "cómo",
    "cuál",
    "cuáles",
    "dónde",
    "el",
    "en",
    "es",
    "la",
    "las",
    "los",
    "por",
    "qué",
    "según",
    "son",
    "tabla",
    "tablas",
    "una",
}
_ENGLISH_MARKERS = {
    "according",
    "are",
    "does",
    "how",
    "is",
    "table",
    "tables",
    "the",
    "what",
    "where",
    "which",
    "with",
}
_PORTUGUESE_EXCLUSIVE_MARKERS = {
    "é",
    "não",
    "quais",
    "são",
    "tabela",
    "tabelas",
}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", text.casefold(), flags=re.UNICODE)


def infer_question_language(text: str) -> SupportedLanguage:
    tokens = _tokens(text)
    spanish_score = sum(token in _SPANISH_MARKERS for token in tokens)
    english_score = sum(token in _ENGLISH_MARKERS for token in tokens)
    if "¿" in text or spanish_score >= english_score:
        return "es"
    return "en"


def text_matches_language(text: str, expected: SupportedLanguage) -> bool:
    """Reject clear language drift while tolerating technical identifiers."""

    tokens = _tokens(text)
    spanish_score = sum(token in _SPANISH_MARKERS for token in tokens)
    english_score = sum(token in _ENGLISH_MARKERS for token in tokens)
    portuguese_score = sum(token in _PORTUGUESE_EXCLUSIVE_MARKERS for token in tokens)

    if expected == "es":
        if portuguese_score >= 2:
            return False
        return not (english_score >= 4 and spanish_score == 0)
    return not (spanish_score >= 4 and english_score == 0)


def normalized_contains(text: str, expected: str) -> bool:
    def normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value.casefold())
        return "".join(char for char in decomposed if not unicodedata.combining(char))

    return normalize(expected) in normalize(text)
