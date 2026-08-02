import logging
import uuid
from typing import Any

from flask import Flask, Response, current_app, g, jsonify
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for every API error."""
    status_code = 500
    code = "internal_server_error"
    message = "An unexpected error occurred."

    def __init__(
            self,
            message: str | None = None,
            *,
            status_code: int | None = None,
            code: str | None = None,
            details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.status_code = status_code or self.status_code
        self.code = code or self.code
        self.details = details


class BadRequestError(APIError):
    status_code = 400
    code = "bad_request"
    message = "Bad request."


class AuthenticationError(APIError):
    status_code = 401
    code = "authentication_failed"
    message = "Authentication is required."


class PermissionDeniedError(APIError):
    status_code = 403
    code = "permission_denied"
    message = "Permission denied."


class NotFoundError(APIError):
    status_code = 404
    code = "not_found"
    message = "Not found."


class ConflictError(APIError):
    status_code = 409
    code = "conflict"
    message = "Request conflicts with current state."


class UnprocessableError(APIError):
    status_code = 422
    code = "validation_failed"
    message = "The request body failed validation."


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> tuple[Response, int]:
    """Build the error that the API will return."""
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(g, "request_id", None),
        }
    }
    if details:
        body["error"]["details"] = details
    return jsonify(body), status_code


def _validation_details(exc: ValidationError) -> list[dict[str, Any]]:
    """Flatten Pydantic validation errors into field/message pairs."""
    return [
        {
            "field": ".".join(str(part) for part in err["loc"]) or "_body",
            "message": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""
    @app.before_request
    def _assign_request_id() -> None:
        g.request_id = uuid.uuid4().hex

    @app.after_request
    def _echo_request_id(response: Response) -> Response:
        if request_id := getattr(g, "request_id", None):
            response.headers["X-Request-ID"] = request_id
        return response

    # For API errors
    @app.errorhandler(APIError)
    def _handle_api_error(exc: APIError) -> tuple[Response, int]:
        logger.info(
            "api_error", extra={"request_id": g.get("request_id"), "code": exc.code}
        )
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    # For validation errors
    @app.errorhandler(ValidationError)
    def _handle_validation_error(exc: ValidationError) -> tuple[Response, int]:
        return error_response(
            422, "validation_failed", "The request body failed validation.",
            _validation_details(exc),
        )

    # For HTTP (Werkzeug) exceptions
    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc: HTTPException) -> tuple[Response, int]:
        return error_response(
            exc.code or 500,
            (exc.name or "error").lower().replace(" ", "_"),
            exc.description or "Request failed.",
        )

    # To raise exceptions in debug
    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception) -> tuple[Response, int]:
        if current_app.debug:
            raise exc
        logger.exception("unhandled_exception", extra={"request_id": g.get("request_id")})
        return error_response(500, "internal_error", "An unexpected error occurred.")
