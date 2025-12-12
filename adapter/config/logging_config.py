"""
Privacy-aware logging configuration.

CRITICAL: Never log PII in standard output.
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from adapter.config.settings import settings
from adapter.utils.privacy import sanitize_for_logging


class JSONFormatter(logging.Formatter):
    """
    Format logs as JSON for structured logging.

    Automatically sanitizes PII from log records.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra"):
            extra_data = sanitize_for_logging(record.extra)
            log_data["extra"] = extra_data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Format logs as human-readable text.

    Automatically sanitizes PII from log records.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as text."""

        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        message = record.getMessage()

        log_line = f"[{timestamp}] {record.levelname:8s} {record.module}:{record.funcName}:{record.lineno} - {message}"

        # Add extra fields if present
        if hasattr(record, "extra"):
            extra_data = sanitize_for_logging(record.extra)
            log_line += f" | {json.dumps(extra_data)}"

        # Add exception info if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)

        return log_line


def setup_logging() -> logging.Logger:
    """
    Configure privacy-aware logging.

    Returns:
        Configured logger instance
    """

    # Create logger
    logger = logging.getLogger("gun_registry_adapter")
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Choose formatter based on config
    if settings.log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Console handler
    if settings.log_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler (audit trail)
    log_file = Path(settings.log_file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Create singleton logger
logger = setup_logging()


def log_with_context(level: str, message: str, **context: Any):
    """
    Log message with extra context (sanitized for PII).

    Args:
        level: Log level ("info", "warning", "error", etc.)
        message: Log message
        **context: Additional context fields
    """

    log_func = getattr(logger, level.lower())

    # Create a LogRecord with extra context
    extra_data = {"extra": context}
    log_func(message, extra=extra_data)
