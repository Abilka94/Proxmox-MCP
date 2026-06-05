"""Network domain read helpers."""

from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


async def network_list(client: PveClient, node: str) -> dict[str, object]:
    """Return network interfaces for a specific node."""

    interfaces = await client.get_network_interfaces(node)
    return {
        "count": len(interfaces),
        "interfaces": [i.model_dump(mode="json") for i in interfaces],
    }
