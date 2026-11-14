"""Custom exception hierarchy for the AI reasoning engine.

Provides strongly typed exceptions for timeouts, rate limits, authentication
failures, and model validation errors without leaking sensitive credentials.
"""


class AIServiceError(Exception):
    """Base exception for all AI subsystem errors."""

    def __init__(self, message: str, details: str = ""):
        super().__init__(message)
        self.message = message
        self.details = details


class AITimeoutError(AIServiceError):
    """Raised when an AI provider call exceeds the configured timeout threshold."""


class AIRateLimitError(AIServiceError):
    """Raised when an AI provider returns HTTP 429 or quota exhaustion."""


class AIAuthenticationError(AIServiceError):
    """Raised when API credentials are missing, invalid, or unauthorized."""


class AIValidationError(AIServiceError):
    """Raised when an AI provider returns malformed JSON or invalid schema."""


class AIUnavailableError(AIServiceError):
    """Raised when the AI provider is disabled, unconfigured, or network unreachable."""
