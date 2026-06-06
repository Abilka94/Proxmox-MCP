from __future__ import annotations

import unittest
from unittest.mock import AsyncMock

from mcp_proxmox.domains.vms import vm_config, vm_list, vm_status
from mcp_proxmox.pve.models.responses import VmConfig, VmResource, VmStatus


class MockPveClient:
    def __init__(self) -> None:
        self.get_vms = AsyncMock()
        self.get_vm_status = AsyncMock()
        self.get_vm_config = AsyncMock()


class VmDomainTests(unittest.IsolatedAsyncioTestCase):
    async def test_vm_list_returns_all_vms(self) -> None:
        client = MockPveClient()
        client.get_vms.return_value = [
            VmResource(
                id="qemu/100", node="pve1", type="qemu", vmid=100, name="web", status="running"
            ),
            VmResource(
                id="qemu/101", node="pve1", type="qemu", vmid=101, name="db", status="stopped"
            ),
        ]

        result = await vm_list(client)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["vms"][0]["name"], "web")
        self.assertEqual(result["vms"][1]["vmid"], 101)

    async def test_vm_list_empty(self) -> None:
        client = MockPveClient()
        client.get_vms.return_value = []
        result = await vm_list(client)
        self.assertEqual(result["count"], 0)

    async def test_vm_status_returns_details(self) -> None:
        client = MockPveClient()
        client.get_vm_status.return_value = VmStatus(
            status="running",
            cpu=0.15,
            mem=2147483648,
            maxmem=4294967296,
            uptime=12345,
            name="web",
            cpus=2,
            tags="production",
        )

        result = await vm_status(client, "pve1", 100)

        self.assertEqual(result["status"], "running")
        self.assertEqual(result["cpu"], 0.15)
        self.assertEqual(result["cpus"], 2)
        self.assertEqual(result["name"], "web")
        self.assertEqual(result["tags"], "production")

    async def test_vm_status_passes_params(self) -> None:
        client = MockPveClient()
        client.get_vm_status.return_value = VmStatus(status="running")

        await vm_status(client, "pve2", 200)

        client.get_vm_status.assert_awaited_once_with("pve2", 200)

    async def test_vm_config_returns_full_config(self) -> None:
        client = MockPveClient()
        client.get_vm_config.return_value = VmConfig(
            name="web",
            vmid=100,
            cores=4,
            memory=8192,
            sockets=1,
            ostype="l26",
            agent=1,
            boot="order=virtio0;ide2;net0",
            bootdisk="virtio0",
            scsihw="virtio-scsi-pci",
            tags="production;web",
            template=0,
        )

        result = await vm_config(client, "pve1", 100)

        self.assertEqual(result["name"], "web")
        self.assertEqual(result["cores"], 4)
        self.assertEqual(result["memory"], 8192)
        self.assertEqual(result["ostype"], "l26")
        self.assertEqual(result["scsihw"], "virtio-scsi-pci")
        self.assertEqual(result["tags"], "production;web")

    async def test_vm_config_passes_params(self) -> None:
        client = MockPveClient()
        client.get_vm_config.return_value = VmConfig(vmid=200)

        await vm_config(client, "pve2", 200)

        client.get_vm_config.assert_awaited_once_with("pve2", 200)


if __name__ == "__main__":
    unittest.main()
