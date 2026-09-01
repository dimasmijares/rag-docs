from __future__ import annotations


def run() -> None:
    import uvicorn

    uvicorn.run("rag_docs.api:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
