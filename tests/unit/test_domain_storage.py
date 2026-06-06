from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.storage import storage_content, storage_list, storage_status
from mcp_proxmox.pve.models.responses import StorageContentItem, StorageResource, StorageStatus


class MockPveClient:
    def __init__(self) -> None:
        self.get_storages = AsyncMock()
        self.get_storage_status = AsyncMock()
        self.get_storage_content = AsyncMock()


class StorageDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_storage_list_returns_all(self) -> None:
        client = MockPveClient()
        client.get_storages.return_value = [
            StorageResource(
                id="storage/local", node="pve1", type="storage", storage="local", status="available"
            ),
            StorageResource(
                id="storage/nfs",
                node="pve1",
                type="storage",
                storage="nfs-backup",
                status="available",
            ),
        ]

        result = await storage_list(client)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["storages"][0]["storage"], "local")

    async def test_storage_list_empty(self) -> None:
        client = MockPveClient()
        client.get_storages.return_value = []
        result = await storage_list(client)
        self.assertEqual(result["count"], 0)

    async def test_storage_status_returns_details(self) -> None:
        client = MockPveClient()
        client.get_storage_status.return_value = StorageStatus(
            total=1073741824000,
            used=536870912000,
            avail=536870912000,
            used_fraction=0.5,
            active=1,
            content="vztmpl,iso,backup",
        )

        result = await storage_status(client, "pve1", "local")

        self.assertEqual(result["total"], 1073741824000)
        self.assertEqual(result["used_fraction"], 0.5)
        self.assertEqual(result["active"], 1)

    async def test_storage_status_passes_params(self) -> None:
        client = MockPveClient()
        client.get_storage_status.return_value = StorageStatus()

        await storage_status(client, "pve2", "nfs-backup")

        client.get_storage_status.assert_awaited_once_with("pve2", "nfs-backup")

    async def test_storage_content_returns_items(self) -> None:
        client = MockPveClient()
        client.get_storage_content.return_value = [
            StorageContentItem(
                volid="local:iso/ubuntu-24.04.iso",
                format="iso",
                size=4294967296,
                content="iso",
            ),
            StorageContentItem(
                volid="local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst",
                format="tar.zst",
                size=2147483648,
                content="vztmpl",
            ),
        ]

        result = await storage_content(client, "pve1", "local")

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["items"][0]["volid"], "local:iso/ubuntu-24.04.iso")
        self.assertEqual(result["items"][1]["content"], "vztmpl")

    async def test_storage_content_empty(self) -> None:
        client = MockPveClient()
        client.get_storage_content.return_value = []
        result = await storage_content(client, "pve1", "local")
        self.assertEqual(result["count"], 0)

    async def test_storage_content_passes_params(self) -> None:
        client = MockPveClient()
        client.get_storage_content.return_value = []

        await storage_content(client, "pve2", "nfs-iso")

        client.get_storage_content.assert_awaited_once_with("pve2", "nfs-iso")


if __name__ == "__main__":
    unittest.main()
