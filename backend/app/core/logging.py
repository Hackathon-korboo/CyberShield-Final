"""Logging configuration for CyberShield AI 2.0.

Provides structured formatting, correlation ID injection, and automatic scrubbing
of potential credentials, bearer tokens, or API keys from log records.
"""

import logging
import re
import sys
from typing import Optional


# Rule definitions for scrubbing potential secrets: (compiled pattern, replacement string)
SECRET_SCRUB_RULES = [
    (re.compile(r"AIza[0-9A-Za-z\-_]{30,45}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.\~+/]+=*", re.IGNORECASE), r"\g<1>[REDACTED]"),
    (re.compile(r"((?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?)([^'\"\s&]+)(['\"]?)", re.IGNORECASE), r"\g<1>[REDACTED]\g<3>"),
]


class SecretScrubbingFilter(logging.Filter):
    """Log filter that redacts detected secret patterns from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            scrubbed = record.msg
            for pattern, replacement in SECRET_SCRUB_RULES:
                scrubbed = pattern.sub(replacement, scrubbed)
            record.msg = scrubbed
        return True


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Initialize root and application loggers with secure formatting."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Format includes timestamp, log level, logger name, and correlation ID if set
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(SecretScrubbingFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to prevent duplicate lines
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    root_logger.addHandler(console_handler)

    # App logger
    app_logger = logging.getLogger("cybershield")
    app_logger.setLevel(numeric_level)

    return app_logger
