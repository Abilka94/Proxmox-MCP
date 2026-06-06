from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.updates import cluster_updates, node_updates
from mcp_proxmox.pve.models.responses import (
    ClusterUpdateEntry,
    NodeUpdateEntry,
)


class MockPveClient:
    def __init__(self) -> None:
        self.get_node_updates = AsyncMock()
        self.get_nodes = AsyncMock()
        self.get_cluster_updates = AsyncMock()


class UpdateDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_node_updates_returns_updates(self) -> None:
        client = MockPveClient()
        client.get_node_updates.return_value = [
            NodeUpdateEntry(
                title="libc6",
                package="libc6",
                version="2.36-9+deb12u7",
                old_version="2.36-9+deb12u6",
                priority="recommended",
            ),
            NodeUpdateEntry(
                title="openssl",
                package="openssl",
                version="3.0.15-1~deb12u1",
                old_version="3.0.14-1~deb12u1",
                priority="security",
            ),
        ]

        result = await node_updates(client, "pve1")

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["updates"][0]["package"], "libc6")
        self.assertEqual(result["updates"][1]["priority"], "security")

    async def test_node_updates_empty(self) -> None:
        client = MockPveClient()
        client.get_node_updates.return_value = []
        result = await node_updates(client, "pve1")
        self.assertEqual(result["count"], 0)

    async def test_node_updates_passes_node(self) -> None:
        client = MockPveClient()
        client.get_node_updates.return_value = []

        await node_updates(client, "pve2")

        client.get_node_updates.assert_awaited_once_with("pve2")

    async def test_cluster_updates_aggregates_across_nodes(self) -> None:
        client = MockPveClient()
        client.get_cluster_updates.return_value = [
            ClusterUpdateEntry(node="pve1", title="libc6", package="libc6", priority="recommended"),
            ClusterUpdateEntry(node="pve2", title="openssl", package="openssl", priority="security"),
            ClusterUpdateEntry(node="pve2", title="nginx", package="nginx", priority="recommended"),
        ]

        result = await cluster_updates(client)

        self.assertEqual(result["total_count"], 3)
        self.assertEqual(result["nodes_with_updates"], 2)
        self.assertEqual(result["updates"][0]["node"], "pve1")
        self.assertEqual(result["updates"][0]["package"], "libc6")
        self.assertEqual(result["updates"][1]["node"], "pve2")
        self.assertEqual(result["updates"][1]["package"], "openssl")

    async def test_cluster_updates_empty(self) -> None:
        client = MockPveClient()
        client.get_cluster_updates.return_value = []

        result = await cluster_updates(client)

        self.assertEqual(result["total_count"], 0)
        self.assertEqual(result["nodes_with_updates"], 0)


if __name__ == "__main__":
    unittest.main()
