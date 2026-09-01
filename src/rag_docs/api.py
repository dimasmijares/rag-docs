from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rag_docs.container import ApplicationContainer
from rag_docs.generation import GenerationError


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
        version="0.1.0",
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
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo completar la indexación: {exc}",
            ) from exc

    @app.post("/api/query")
    def query_documents(request: QueryRequest) -> dict[str, Any]:
        try:
            return app.state.container.query.query(request.question).model_dump()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except GenerationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo consultar el índice: {exc}",
            ) from exc

    @app.get("/api/generator")
    def get_generator() -> dict[str, Any]:
        return app.state.container.generator_profiles_state()

    @app.post("/api/generator/check")
    def check_generator(request: GeneratorProfileRequest) -> dict[str, Any]:
        try:
            return app.state.container.check_generator_profile(request.profile)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except GenerationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/api/generator/activate")
    def activate_generator(request: GeneratorProfileRequest) -> dict[str, Any]:
        try:
            return app.state.container.activate_generator_profile(
                request.profile,
                request.model,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except GenerationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return app


app = create_app()
