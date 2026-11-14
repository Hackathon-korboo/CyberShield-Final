"""Application exception definitions and global exception handlers.

Ensures all errors return consistent, sanitized JSON responses conforming to
the CyberShield standard error envelope without leaking internal secrets,
file paths, or stack traces.
"""

from typing import Any, Dict, List, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class CyberShieldBaseException(Exception):
    """Base exception for all domain-specific CyberShield errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[List[Dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or []


class ConfigurationError(CyberShieldBaseException):
    """Raised when application configuration is invalid or missing required variables."""

    def __init__(self, message: str, details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class SSRFProtectionError(CyberShieldBaseException):
    """Raised when an inbound target URL resolves to a protected, private, or loopback IP."""

    def __init__(self, message: str = "Target URL violates SSRF safety policy.", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            code="SSRF_PROTECTION_VIOLATION",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class ServiceUnavailableError(CyberShieldBaseException):
    """Raised when an external dependency (AI provider, blockchain RPC) is unavailable."""

    def __init__(self, message: str = "External subsystem currently unavailable.", details: Optional[List[Dict[str, Any]]] = None):
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


def get_correlation_id(request: Request) -> Optional[str]:
    """Extract correlation ID from request state or headers."""
    return getattr(request.state, "correlation_id", request.headers.get("X-Correlation-ID"))


async def cybershield_exception_handler(request: Request, exc: CyberShieldBaseException) -> JSONResponse:
    """Handle custom application exceptions."""
    correlation_id = get_correlation_id(request)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "correlation_id": correlation_id,
                "details": exc.details,
            },
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard Starlette / FastAPI HTTPExceptions."""
    correlation_id = get_correlation_id(request)
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": str(exc.detail),
                "correlation_id": correlation_id,
                "details": [],
            },
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic request validation errors."""
    correlation_id = get_correlation_id(request)
    details = []
    for error in exc.errors():
        field_loc = " -> ".join(str(loc) for loc in error.get("loc", []))
        details.append({
            "field": field_loc,
            "message": error.get("msg", "Invalid value"),
            "error_code": error.get("type", "value_error"),
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed for the requested resource.",
                "correlation_id": correlation_id,
                "details": details,
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler for unhandled internal errors, preventing secret or trace leakage."""
    correlation_id = get_correlation_id(request)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred. Please reference the correlation ID for investigation.",
                "correlation_id": correlation_id,
                "details": [],
            },
        },
    )
