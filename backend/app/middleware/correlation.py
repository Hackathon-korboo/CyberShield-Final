"""Correlation ID Middleware for distributed request tracing.

Assigns or preserves an `X-Correlation-ID` header across each HTTP transaction.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

CORRELATION_HEADER_NAME = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that injects a unique correlation ID into request state and response headers."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract existing or generate new correlation ID
        correlation_id = request.headers.get(CORRELATION_HEADER_NAME)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in request state for downstream handlers and exceptions
        request.state.correlation_id = correlation_id

        # Execute downstream request
        response = await call_next(request)

        # Attach header to outgoing response
        response.headers[CORRELATION_HEADER_NAME] = correlation_id
        return response
