from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.network import network_list
from mcp_proxmox.pve.models.responses import NetworkInterface


class MockPveClient:
    def __init__(self) -> None:
        self.get_network_interfaces = AsyncMock()


class NetworkDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_network_list_returns_interfaces(self) -> None:
        client = MockPveClient()
        client.get_network_interfaces.return_value = [
            NetworkInterface(
                iface="vmbr0", method="static", type="bridge", active=1, cidr="10.0.0.1/24"
            ),
            NetworkInterface(
                iface="enp1s0", method="static", type="eth", active=1, cidr="192.168.1.100/24"
            ),
        ]

        result = await network_list(client, "pve1")

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["interfaces"][0]["iface"], "vmbr0")
        self.assertEqual(result["interfaces"][1]["cidr"], "192.168.1.100/24")

    async def test_network_list_empty(self) -> None:
        client = MockPveClient()
        client.get_network_interfaces.return_value = []
        result = await network_list(client, "pve1")
        self.assertEqual(result["count"], 0)

    async def test_network_list_passes_node(self) -> None:
        client = MockPveClient()
        client.get_network_interfaces.return_value = []

        await network_list(client, "pve2")

        client.get_network_interfaces.assert_awaited_once_with("pve2")


if __name__ == "__main__":
    unittest.main()
