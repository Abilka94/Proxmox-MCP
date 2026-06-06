"""LXC container domain read helpers."""

from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


async def container_list(client: PveClient) -> dict[str, object]:
    """Return all LXC containers in the cluster."""

    containers = await client.get_containers()
    return {
        "count": len(containers),
        "containers": [c.model_dump(mode="json") for c in containers],
    }


async def container_status(client: PveClient, node: str, vmid: int) -> dict[str, object]:
    """Return detailed status for a specific container."""

    status = await client.get_container_status(node, vmid)
    return status.model_dump(mode="json")


async def container_config(client: PveClient, node: str, vmid: int) -> dict[str, object]:
    """Return full configuration for a specific container."""

    config = await client.get_container_config(node, vmid)
    return config.model_dump(mode="json")
