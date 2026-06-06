from __future__ import annotations

import asyncio
import time

from mcp_proxmox.pve.client import PveClient
from mcp_proxmox.pve.client.core import PveApiError

_MAX_LOG_LINES = 5000
_MAX_BACKOFF = 30.0


async def task_list(
    client: PveClient,
    *,
    node: str | None = None,
    user: str | None = None,
    vmid: int | None = None,
    type_filter: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, object]:
    entries = await client.get_tasks(
        node=node,
        user=user,
        vmid=vmid,
        type_filter=type_filter,
        status=status,
        limit=limit,
    )
    return {
        "count": len(entries),
        "tasks": [entry.model_dump(mode="json") for entry in entries],
    }


async def task_status(
    client: PveClient,
    upid: str,
    *,
    node: str | None = None,
) -> dict[str, object]:
    status = await client.get_task_status(upid, node=node)
    return {
        "upid": upid,
        **status.model_dump(mode="json"),
    }


async def task_log(
    client: PveClient,
    upid: str,
    node: str,
    *,
    start: int | None = None,
) -> dict[str, object]:
    entries = await client.get_task_log(node, upid, start=start)
    total = len(entries)
    lines: list[dict[str, object]] = []
    for entry in entries:
        line: dict[str, object] = {"text": entry.t}
        if entry.n is not None:
            line["lineno"] = entry.n
        lines.append(line)
    return {
        "upid": upid,
        "lines": lines,
        "total_lines": total,
    }


def _classify_error(exc: PveApiError) -> str:
    if exc.status_code is None:
        return "transient"
    if exc.status_code in (404, 501):
        return "not_found"
    if 400 <= exc.status_code < 500:
        return "client_error"
    return "transient"


def _elapsed_since(start: float) -> float:
    return round(time.monotonic() - start, 1)


async def task_wait(
    client: PveClient,
    upid: str,
    *,
    node: str | None = None,
    timeout: int = 120,
    poll_interval: float = 1.0,
) -> dict[str, object]:
    start = time.monotonic()
    last_status: str | None = None

    while True:
        elapsed = _elapsed_since(start)
        if elapsed >= timeout:
            return {
                "upid": upid,
                "status": last_status or "unknown",
                "completed": False,
                "timed_out": True,
                "wait_seconds": float(timeout),
            }

        try:
            result = await task_status(client, upid, node=node)
        except PveApiError as exc:
            category = _classify_error(exc)
            if category == "not_found":
                return {
                    "upid": upid,
                    "completed": False,
                    "error": "task_not_found",
                    "wait_seconds": _elapsed_since(start),
                }
            if category == "client_error":
                return {
                    "upid": upid,
                    "completed": False,
                    "error": "api_error",
                    "detail": str(exc),
                    "wait_seconds": _elapsed_since(start),
                }
            await asyncio.sleep(min(poll_interval * 2, _MAX_BACKOFF))
            continue

        last_status = result.get("status")

        if last_status == "stopped":
            response: dict[str, object] = {
                "upid": upid,
                "status": "stopped",
                "completed": True,
                "wait_seconds": _elapsed_since(start),
            }
            exitstatus = result.get("exitstatus")
            if exitstatus is not None:
                response["exitstatus"] = exitstatus
            return response

        await asyncio.sleep(poll_interval)


async def task_follow(
    client: PveClient,
    upid: str,
    node: str,
    *,
    timeout: int = 120,
    poll_interval: float = 1.0,
) -> dict[str, object]:
    start = time.monotonic()
    last_status: str | None = None
    accumulated_lines: list[dict[str, object]] = []
    max_lineno: int = -1
    log_truncated: bool = False
    first_cycle: bool = True

    while True:
        elapsed = _elapsed_since(start)
        if elapsed >= timeout:
            return {
                "upid": upid,
                "status": last_status or "unknown",
                "completed": False,
                "timed_out": True,
                "wait_seconds": float(timeout),
                "lines": accumulated_lines,
                "total_lines": len(accumulated_lines),
            }

        try:
            result = await task_status(client, upid, node=node)
        except PveApiError as exc:
            category = _classify_error(exc)
            if category == "not_found":
                return {
                    "upid": upid,
                    "completed": False,
                    "error": "task_not_found",
                    "wait_seconds": _elapsed_since(start),
                    "lines": accumulated_lines,
                    "total_lines": len(accumulated_lines),
                }
            if category == "client_error":
                return {
                    "upid": upid,
                    "completed": False,
                    "error": "api_error",
                    "detail": str(exc),
                    "wait_seconds": _elapsed_since(start),
                    "lines": accumulated_lines,
                    "total_lines": len(accumulated_lines),
                }
            await asyncio.sleep(min(poll_interval * 2, _MAX_BACKOFF))
            continue

        last_status = result.get("status")

        if not log_truncated:
            try:
                log_start: int | None = None if first_cycle else max_lineno + 1
                log_result = await task_log(client, upid, node, start=log_start)
            except PveApiError as exc:
                category = _classify_error(exc)
                if category in ("not_found", "client_error"):
                    return {
                        "upid": upid,
                        "completed": False,
                        "error": "api_error",
                        "detail": str(exc),
                        "wait_seconds": _elapsed_since(start),
                        "lines": accumulated_lines,
                        "total_lines": len(accumulated_lines),
                    }
            else:
                for line in log_result.get("lines", []):
                    lineno = line.get("lineno")
                    if lineno is None:
                        accumulated_lines.append(line)
                    elif lineno > max_lineno:
                        accumulated_lines.append(line)
                        max_lineno = lineno
                if len(accumulated_lines) >= _MAX_LOG_LINES:
                    log_truncated = True
                    accumulated_lines = accumulated_lines[:_MAX_LOG_LINES]

            first_cycle = False

        if last_status == "stopped":
            response: dict[str, object] = {
                "upid": upid,
                "status": "stopped",
                "completed": True,
                "wait_seconds": _elapsed_since(start),
                "lines": accumulated_lines,
                "total_lines": len(accumulated_lines),
            }
            exitstatus = result.get("exitstatus")
            if exitstatus is not None:
                response["exitstatus"] = exitstatus
            if log_truncated:
                response["log_truncated"] = True
            return response

        await asyncio.sleep(poll_interval)
