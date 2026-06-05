"""Structured logging setup."""

from mcp_proxmox.logging.context import (
    correlation_context,
    get_correlation_id,
    set_correlation_id,
)
from mcp_proxmox.logging.setup import configure_logging, get_logger, redact

__all__ = [
    "configure_logging",
    "correlation_context",
    "get_correlation_id",
    "get_logger",
    "redact",
    "set_correlation_id",
]
