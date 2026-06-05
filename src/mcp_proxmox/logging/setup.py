"""Structured logging setup for MCP-Proxmox."""

from __future__ import annotations

import json
import logging as stdlib_logging
import sys
from collections.abc import Mapping
from typing import Any, TextIO

from mcp_proxmox.config.models import LogFormat, LoggingConfig, LogLevel
from mcp_proxmox.logging.context import get_correlation_id

REDACTED = "[REDACTED]"
SENSITIVE_PARTS = ("token", "secret", "password", "authorization")
STANDARD_RECORD_KEYS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonFormatter(stdlib_logging.Formatter):
    """JSON-lines formatter with correlation id and secret redaction."""

    def format(self, record: stdlib_logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
            "correlation_id": get_correlation_id(),
        }
        event.update(_extra_fields(record))
        if record.exc_info:
            event["exception"] = self.formatException(record.exc_info)
        return json.dumps(redact(event), ensure_ascii=False, sort_keys=True)


class ConsoleFormatter(stdlib_logging.Formatter):
    """Human-readable formatter for local development."""

    def format(self, record: stdlib_logging.LogRecord) -> str:
        correlation_id = get_correlation_id() or "-"
        return f"{record.levelname} [{correlation_id}] {record.name}: {record.getMessage()}"


def configure_logging(
    config: LoggingConfig | None = None,
    *,
    level: str | LogLevel | None = None,
    log_format: str | LogFormat | None = None,
    stream: TextIO | None = None,
) -> None:
    """Configure root logging for the application."""

    selected_level = _enum_value(level or (config.level if config else LogLevel.INFO))
    selected_format = _enum_value(log_format or (config.format if config else LogFormat.CONSOLE))

    handler = stdlib_logging.StreamHandler(stream or sys.stdout)
    if selected_format == LogFormat.JSON.value:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root = stdlib_logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(selected_level)


def get_logger(name: str) -> stdlib_logging.Logger:
    """Return an application logger."""

    return stdlib_logging.getLogger(name)


def redact(value: Any) -> Any:
    """Redact sensitive values by key name."""

    if isinstance(value, Mapping):
        return {
            key: REDACTED if _is_sensitive_key(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def _extra_fields(record: stdlib_logging.LogRecord) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in STANDARD_RECORD_KEYS and not key.startswith("_")
    }


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_PARTS)


def _enum_value(value: str | LogLevel | LogFormat) -> str:
    if isinstance(value, LogLevel | LogFormat):
        return value.value
    return value
