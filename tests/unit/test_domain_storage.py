from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.storage import storage_list, storage_status
from mcp_proxmox.pve.models.responses import StorageResource, StorageStatus


class MockPveClient:
    def __init__(self) -> None:
        self.get_storages = AsyncMock()
        self.get_storage_status = AsyncMock()


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


if __name__ == "__main__":
    unittest.main()
