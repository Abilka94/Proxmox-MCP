from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.containers import container_config, container_list, container_status
from mcp_proxmox.pve.models.responses import LxcConfig, LxcResource, LxcStatus


class MockPveClient:
    def __init__(self) -> None:
        self.get_containers = AsyncMock()
        self.get_container_status = AsyncMock()
        self.get_container_config = AsyncMock()


class ContainerDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_container_list_returns_all(self) -> None:
        client = MockPveClient()
        client.get_containers.return_value = [
            LxcResource(
                id="lxc/300", node="pve1", type="lxc", vmid=300, name="ubuntu-ct", status="running"
            ),
            LxcResource(
                id="lxc/301", node="pve2", type="lxc", vmid=301, name="debian-ct", status="stopped"
            ),
        ]

        result = await container_list(client)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["containers"][0]["name"], "ubuntu-ct")

    async def test_container_list_empty(self) -> None:
        client = MockPveClient()
        client.get_containers.return_value = []
        result = await container_list(client)
        self.assertEqual(result["count"], 0)

    async def test_container_status_returns_details(self) -> None:
        client = MockPveClient()
        client.get_container_status.return_value = LxcStatus(
            status="running",
            cpu=0.05,
            mem=524288000,
            maxmem=1073741824,
            uptime=6789,
            name="ubuntu-ct",
            cpus=1,
            tags="dev",
        )

        result = await container_status(client, "pve1", 300)

        self.assertEqual(result["status"], "running")
        self.assertEqual(result["cpu"], 0.05)
        self.assertEqual(result["cpus"], 1)
        self.assertEqual(result["name"], "ubuntu-ct")

    async def test_container_status_passes_params(self) -> None:
        client = MockPveClient()
        client.get_container_status.return_value = LxcStatus(status="running")

        await container_status(client, "pve2", 301)

        client.get_container_status.assert_awaited_once_with("pve2", 301)

    async def test_container_config_returns_full_config(self) -> None:
        client = MockPveClient()
        client.get_container_config.return_value = LxcConfig(
            hostname="ubuntu-ct",
            vmid=300,
            cores=2,
            memory=2048,
            swap=512,
            ostype="ubuntu",
            rootfs="local-lvm:8",
            tags="dev;ubuntu",
        )

        result = await container_config(client, "pve1", 300)

        self.assertEqual(result["hostname"], "ubuntu-ct")
        self.assertEqual(result["cores"], 2)
        self.assertEqual(result["memory"], 2048)
        self.assertEqual(result["ostype"], "ubuntu")
        self.assertEqual(result["rootfs"], "local-lvm:8")

    async def test_container_config_passes_params(self) -> None:
        client = MockPveClient()
        client.get_container_config.return_value = LxcConfig(vmid=301)

        await container_config(client, "pve2", 301)

        client.get_container_config.assert_awaited_once_with("pve2", 301)


if __name__ == "__main__":
    unittest.main()
