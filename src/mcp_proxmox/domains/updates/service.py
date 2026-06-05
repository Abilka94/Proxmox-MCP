"""Update domain read helpers."""

from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


async def node_updates(client: PveClient, node: str) -> dict[str, object]:
    """Return available APT updates for a specific node."""

    updates = await client.get_node_updates(node)
    return {
        "count": len(updates),
        "updates": [u.model_dump(mode="json") for u in updates],
    }
