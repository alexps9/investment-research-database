"""
Structured logging configuration for production and development environments

Production: JSON format for log aggregation and parsing
Development: Human-readable format for local debugging
"""

import json
import logging
import os
from datetime import datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging in production

    Outputs logs in JSON format with timestamp, level, message, module, function, and line number
    Includes exception information if present
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string

        Args:
            record: LogRecord object from Python logging

        Returns:
            JSON string with log information
        """
        log_entry: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging() -> logging.Logger:
    """
    Setup application logging configuration

    Behavior:
    - Production (NODE_ENV=production): JSON format for log aggregation
    - Development (NODE_ENV=development): Human-readable format
    - Log level: Controlled by LOG_LEVEL environment variable (default: info)

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging()
        >>> logger.info("Application starting")
        >>> logger.error("Error occurred", exc_info=True)
    """
    # Get environment variables
    log_level = os.getenv("LOG_LEVEL", "info").upper()
    node_env = os.getenv("NODE_ENV", "production")

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler()

    # Choose formatter based on environment
    if node_env == "production":
        # JSON format for production (log aggregation friendly)
        handler.setFormatter(JSONFormatter())
    else:
        # Human-readable format for development
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    logger.addHandler(handler)

    # Log initial configuration
    logger.info(
        f"Logging configured: level={log_level}, environment={node_env}, "
        f"format={'JSON' if node_env == 'production' else 'human-readable'}"
    )

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given module name."""
    return logging.getLogger(name)
