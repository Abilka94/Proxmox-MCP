from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.nodes import node_status
from mcp_proxmox.pve.models.responses import NodeStatus


class MockPveClient:
    def __init__(self) -> None:
        self.get_node = AsyncMock()


class NodeDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_node_status_returns_detailed_info(self) -> None:
        client = MockPveClient()
        client.get_node.return_value = NodeStatus(
            cpu=0.25,
            uptime=12345,
            pveversion="8.2.4",
            kversion="6.8.12-2-pve",
            loadavg=[0.1, 0.2, 0.3],
            memory={"total": 17179869184, "used": 8589934592, "free": 8589934592},
            rootfs={"total": 107374182400, "used": 53687091200, "avail": 53687091200},
            swap={"total": 4294967296, "used": 0, "free": 4294967296},
            cpuinfo={"model": "AMD EPYC 7452", "cpus": 8},
        )

        result = await node_status(client, "pve1")

        self.assertEqual(result["cpu"], 0.25)
        self.assertEqual(result["uptime"], 12345)
        self.assertEqual(result["pveversion"], "8.2.4")
        self.assertEqual(result["kversion"], "6.8.12-2-pve")
        self.assertEqual(result["loadavg"], [0.1, 0.2, 0.3])
        self.assertIn("memory", result)
        self.assertIn("rootfs", result)
        self.assertIn("swap", result)
        self.assertIn("cpuinfo", result)

    async def test_node_status_uses_correct_node_name(self) -> None:
        client = MockPveClient()
        client.get_node.return_value = NodeStatus(cpu=0.1)

        await node_status(client, "pve2")

        client.get_node.assert_awaited_once_with("pve2")


if __name__ == "__main__":
    unittest.main()
