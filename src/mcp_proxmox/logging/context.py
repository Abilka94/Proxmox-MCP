"""Correlation context for logs and MCP requests."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Return the current correlation id, if one is bound."""

    return _correlation_id.get()


def set_correlation_id(correlation_id: str | None) -> None:
    """Bind a correlation id to the current context."""

    _correlation_id.set(correlation_id)


@contextmanager
def correlation_context(correlation_id: str) -> Iterator[None]:
    """Temporarily bind a correlation id."""

    token = _correlation_id.set(correlation_id)
    try:
        yield
    finally:
        _correlation_id.reset(token)
