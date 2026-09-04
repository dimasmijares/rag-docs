from __future__ import annotations

from rag_docs.contracts.value_objects import ErrorKind

# Maps the closed ErrorKind taxonomy to HTTP status codes. api.py uses this
# instead of collapsing every failure into 503 with the exception text, which
# leaks internal detail to the client.
HTTP_STATUS_BY_ERROR_KIND: dict[ErrorKind, int] = {
    ErrorKind.VALIDATION: 400,
    ErrorKind.AUTHORIZATION: 403,
    ErrorKind.NOT_FOUND: 404,
    ErrorKind.DEPENDENCY_UNAVAILABLE: 503,
    ErrorKind.TIMEOUT: 504,
    ErrorKind.INVALID_MODEL_OUTPUT: 502,
}


class AppError(RuntimeError):
    """Base for internal errors that carry a closed ``ErrorKind`` instead of a
    free-text message meant for the client."""

    def __init__(self, kind: ErrorKind, message: str) -> None:
        super().__init__(message)
        self.kind = kind
        self.message = message


def http_status_for(kind: ErrorKind) -> int:
    return HTTP_STATUS_BY_ERROR_KIND[kind]
