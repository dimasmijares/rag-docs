from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_docs import __version__
from rag_docs.container import ApplicationContainer
from rag_docs.contracts import AppError, ErrorKind, http_status_for
from rag_docs.generation import GenerationError, InvalidGeneratedResponse

logger = logging.getLogger(__name__)


def _error(kind: ErrorKind, message: str) -> HTTPException:
    """Map the closed ``ErrorKind`` taxonomy to an HTTP response without ever
    filtering an internal exception's text to the client (``ADR-RAG-010``)."""
    return HTTPException(status_code=http_status_for(kind), detail=message)


class IndexRequest(BaseModel):
    source_ids: list[str] | None = None


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class GeneratorProfileRequest(BaseModel):
    profile: Literal["local", "remote"]
    model: str | None = Field(default=None, min_length=1, max_length=200)


def create_app(container: ApplicationContainer | Any | None = None) -> FastAPI:
    app = FastAPI(
        title="rag-docs",
        version=__version__,
        description="PoC local de consulta documental con fuentes trazables.",
    )
    app.state.container = container or ApplicationContainer()
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index_page() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/sources")
    def get_sources() -> dict[str, Any]:
        definitions = app.state.container.source_definitions
        return {
            "sources": [
                {
                    "id": source.id,
                    "type": source.type,
                    "root": str(source.root),
                    "available": source.root.is_dir(),
                    "include": source.include,
                    "exclude": source.exclude,
                }
                for source in definitions
            ]
        }

    @app.post("/api/index")
    def index_documents(request: IndexRequest | None = None) -> dict[str, Any]:
        try:
            source_ids = request.source_ids if request else None
            return app.state.container.indexing.index(source_ids).model_dump()
        except ValueError as exc:
            raise _error(ErrorKind.VALIDATION, str(exc)) from exc
        except AppError as exc:
            raise _error(exc.kind, exc.message) from exc
        except Exception as exc:
            logger.exception("No se pudo completar la indexación")
            raise _error(
                ErrorKind.DEPENDENCY_UNAVAILABLE,
                "No se pudo completar la indexación.",
            ) from exc

    @app.post("/api/query")
    def query_documents(request: QueryRequest) -> dict[str, Any]:
        try:
            return app.state.container.query.query(request.question).model_dump()
        except ValueError as exc:
            raise _error(ErrorKind.VALIDATION, str(exc)) from exc
        except InvalidGeneratedResponse as exc:
            raise _error(ErrorKind.INVALID_MODEL_OUTPUT, str(exc)) from exc
        except GenerationError as exc:
            raise _error(ErrorKind.DEPENDENCY_UNAVAILABLE, str(exc)) from exc
        except AppError as exc:
            raise _error(exc.kind, exc.message) from exc
        except Exception as exc:
            logger.exception("No se pudo consultar el índice")
            raise _error(
                ErrorKind.DEPENDENCY_UNAVAILABLE,
                "No se pudo consultar el índice.",
            ) from exc

    @app.get("/api/generator")
    def get_generator() -> dict[str, Any]:
        return app.state.container.generator_profiles_state()

    @app.post("/api/generator/check")
    def check_generator(request: GeneratorProfileRequest) -> dict[str, Any]:
        try:
            return app.state.container.check_generator_profile(request.profile)
        except ValueError as exc:
            raise _error(ErrorKind.VALIDATION, str(exc)) from exc
        except GenerationError as exc:
            raise _error(ErrorKind.DEPENDENCY_UNAVAILABLE, str(exc)) from exc

    @app.post("/api/generator/activate")
    def activate_generator(request: GeneratorProfileRequest) -> dict[str, Any]:
        try:
            return app.state.container.activate_generator_profile(
                request.profile,
                request.model,
            )
        except ValueError as exc:
            raise _error(ErrorKind.VALIDATION, str(exc)) from exc
        except GenerationError as exc:
            raise _error(ErrorKind.DEPENDENCY_UNAVAILABLE, str(exc)) from exc

    return app


app = create_app()
