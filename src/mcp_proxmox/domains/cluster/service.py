"""Cluster domain read helpers."""

from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


async def cluster_info(client: PveClient) -> dict[str, object]:
    """Return cluster information with node summary."""

    entries = await client.get_cluster_status()

    cluster_entry: dict[str, object] = {}
    nodes: list[dict[str, object]] = []

    for entry in entries:
        d = entry.model_dump(mode="json")
        if d.get("type") == "cluster":
            cluster_entry = d
        else:
            nodes.append(d)

    online = sum(1 for n in nodes if n.get("online") == 1)

    return {
        "name": cluster_entry.get("name"),
        "version": cluster_entry.get("version"),
        "quorate": cluster_entry.get("quorate"),
        "nodes": {
            "total": len(nodes),
            "online": online,
            "offline": len(nodes) - online,
            "members": nodes,
        },
    }
