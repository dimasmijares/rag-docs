from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator


class GenerationError(RuntimeError):
    pass


class InvalidGeneratedResponse(GenerationError):
    pass


@dataclass(frozen=True, slots=True)
class GeneratorCapabilities:
    structured_output: bool
    vision: bool
    streaming: bool


@dataclass(frozen=True, slots=True)
class GeneratorHealth:
    ready: bool
    endpoint: str
    selected_model: str
    available_models: tuple[str, ...]


class GeneratedClaim(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    citations: list[int] = Field(min_length=1)


class GeneratedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["grounded", "insufficient_evidence"]
    language: Literal["es", "en"]
    claims: list[GeneratedClaim]
    unanswered_parts: list[str]

    @model_validator(mode="after")
    def validate_status_content(self) -> GeneratedResponse:
        if self.status == "grounded" and not self.claims:
            raise ValueError("Una respuesta grounded necesita afirmaciones")
        if self.status == "grounded" and self.unanswered_parts:
            raise ValueError("Una respuesta grounded no puede dejar partes sin responder")
        return self


class Generator(Protocol):
    @property
    def model_name(self) -> str: ...

    @property
    def capabilities(self) -> GeneratorCapabilities: ...

    def health(self) -> GeneratorHealth: ...

    def generate(
        self,
        question: str,
        context: str,
        *,
        validation_feedback: str | None = None,
    ) -> GeneratedResponse: ...


class OllamaGenerator:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        timeout: float = 180.0,
        temperature: float = 0.0,
        seed: int = 0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._model_name = model_name
        self.timeout = timeout
        self.temperature = temperature
        self.seed = seed

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def capabilities(self) -> GeneratorCapabilities:
        return GeneratorCapabilities(
            structured_output=True,
            vision=False,
            streaming=False,
        )

    def health(self) -> GeneratorHealth:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=min(self.timeout, 10))
            response.raise_for_status()
            available = tuple(
                str(model["name"])
                for model in response.json().get("models", [])
                if model.get("name")
            )
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise GenerationError(
                f"Ollama no está disponible en {self.base_url}: {exc}"
            ) from exc
        return GeneratorHealth(
            ready=self._model_name in available,
            endpoint=self.base_url,
            selected_model=self._model_name,
            available_models=available,
        )

    def generate(
        self,
        question: str,
        context: str,
        *,
        validation_feedback: str | None = None,
    ) -> GeneratedResponse:
        system = (
            "Eres un asistente de documentación técnica. Usa exclusivamente CONTEXTO. "
            "Analiza todos los elementos solicitados: si la pregunta tiene varias partes, "
            "responde cada una en una afirmación separada. Si pide elementos en plural, "
            "enumera todos los que estén respaldados. Copia literalmente identificadores "
            "técnicos completos (tablas, variables, ETL, procedimientos, rutas y códigos); "
            "no los sustituyas por etiquetas abreviadas si el contexto contiene el nombre "
            "completo o cualificado con base y esquema. Cita el fragmento que contiene "
            "literalmente cada identificador utilizado, no una descripción general. Usa "
            "exactamente el idioma de la pregunta, sin mezclar idiomas. "
            "Cada afirmación debe ser una frase autosuficiente y sus citations deben contener "
            "los números [n] del contexto que la respaldan. No escribas [n] dentro de text. "
            "Devuelve status=grounded sólo si respondes todas las partes. Si falta evidencia, "
            "usa status=insufficient_evidence y describe cada carencia en unanswered_parts."
        )
        feedback = (
            f"\n\nCORRECCIÓN OBLIGATORIA\n{validation_feedback}"
            if validation_feedback
            else ""
        )
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self._model_name,
                    "stream": False,
                    "format": GeneratedResponse.model_json_schema(),
                    "messages": [
                        {"role": "system", "content": system},
                        {
                            "role": "user",
                            "content": (
                                f"CONTEXTO\n{context}\n\nPREGUNTA\n{question}{feedback}"
                            ),
                        },
                    ],
                    "options": {
                        "temperature": self.temperature,
                        "seed": self.seed,
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            content = response.json()["message"]["content"].strip()
            if not content:
                raise GenerationError("Ollama devolvió una respuesta vacía")
        except GenerationError:
            raise
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise GenerationError(
                f"No se pudo generar una respuesta estructurada con Ollama "
                f"({self.base_url}): {exc}"
            ) from exc
        try:
            return GeneratedResponse.model_validate_json(content)
        except ValidationError as exc:
            raise InvalidGeneratedResponse(
                f"Ollama no respetó el esquema de respuesta: {exc}"
            ) from exc
