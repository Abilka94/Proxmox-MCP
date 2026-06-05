"""Node domain read helpers."""

from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


async def list_nodes(client: PveClient) -> dict[str, object]:
    """Return a MCP-friendly node list payload."""

    nodes = await client.get_nodes()
    return {
        "count": len(nodes),
        "nodes": [node.model_dump(mode="json") for node in nodes],
    }


async def node_status(client: PveClient, node_name: str) -> dict[str, object]:
    """Return detailed status for a specific node."""

    status = await client.get_node(node_name)
    return status.model_dump(mode="json")
