"""Проверка исходных идентификаторов task перед обращением к API."""

import re

UPID_PATTERN = (
    r"UPID:([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?):"
    r"[0-9A-Fa-f]{8}:[0-9A-Fa-f]{8,9}:[0-9A-Fa-f]{8}:"
    r"[^:\s/]+:[^:\s/]*:[^:\s/]+:"
)
_UPID = re.compile(UPID_PATTERN)


class TaskCancelInputError(ValueError):
    """Недопустимые аргументы task_cancel."""


def validate_task_identity(node: str, upid: str) -> None:
    match = _UPID.fullmatch(upid) if isinstance(upid, str) else None
    if not match or not isinstance(node, str) or node != match[1]:
        raise TaskCancelInputError("Требуются исходный UPID и совпадающее имя ноды")
