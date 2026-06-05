from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.cluster import cluster_info
from mcp_proxmox.pve.models.responses import ClusterStatusEntry


class MockPveClient:
    def __init__(self) -> None:
        self.get_cluster_status = AsyncMock()


class ClusterDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_cluster_info_returns_cluster_and_nodes(self) -> None:
        client = MockPveClient()
        client.get_cluster_status.return_value = [
            ClusterStatusEntry(type="cluster", name="pve", version=1, quorate=1),
            ClusterStatusEntry(type="node", name="pve1", online=1),
            ClusterStatusEntry(type="node", name="pve2", online=1),
            ClusterStatusEntry(type="node", name="pve3", online=0),
        ]

        result = await cluster_info(client)

        self.assertEqual(result["name"], "pve")
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["quorate"], 1)
        self.assertEqual(result["nodes"]["total"], 3)
        self.assertEqual(result["nodes"]["online"], 2)
        self.assertEqual(result["nodes"]["offline"], 1)

    async def test_cluster_info_with_single_node(self) -> None:
        client = MockPveClient()
        client.get_cluster_status.return_value = [
            ClusterStatusEntry(type="cluster", name="pve", version=1),
            ClusterStatusEntry(type="node", name="pve1", online=1),
        ]

        result = await cluster_info(client)

        self.assertEqual(result["name"], "pve")
        self.assertEqual(result["nodes"]["total"], 1)
        self.assertEqual(result["nodes"]["online"], 1)

    async def test_cluster_info_empty_nodes_is_valid(self) -> None:
        client = MockPveClient()
        client.get_cluster_status.return_value = [
            ClusterStatusEntry(type="cluster", name="pve"),
        ]

        result = await cluster_info(client)

        self.assertEqual(result["name"], "pve")
        self.assertEqual(result["nodes"]["total"], 0)
        self.assertEqual(result["nodes"]["members"], [])


if __name__ == "__main__":
    unittest.main()
