from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


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
