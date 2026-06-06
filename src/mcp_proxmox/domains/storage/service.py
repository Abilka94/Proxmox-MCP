"""Storage domain read helpers."""

from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


async def storage_list(client: PveClient) -> dict[str, object]:
    """Return all storage resources in the cluster."""

    storages = await client.get_storages()
    return {
        "count": len(storages),
        "storages": [s.model_dump(mode="json") for s in storages],
    }


async def storage_status(client: PveClient, node: str, storage: str) -> dict[str, object]:
    """Return detailed status for a specific storage."""

    status = await client.get_storage_status(node, storage)
    return status.model_dump(mode="json")


async def storage_content(client: PveClient, node: str, storage: str) -> dict[str, object]:
    """Return content list (ISOs, templates, backups) for a specific storage."""

    items = await client.get_storage_content(node, storage)
    return {
        "count": len(items),
        "items": [item.model_dump(mode="json") for item in items],
    }
