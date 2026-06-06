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


async def cluster_updates(client: PveClient) -> dict[str, object]:
    """Return available APT updates across all cluster nodes."""

    updates = await client.get_cluster_updates()

    nodes_with_updates: dict[str, int] = {}
    for u in updates:
        nodes_with_updates[u.node] = nodes_with_updates.get(u.node, 0) + 1

    return {
        "total_count": len(updates),
        "nodes_with_updates": len(nodes_with_updates),
        "updates": [u.model_dump(mode="json") for u in updates],
    }
