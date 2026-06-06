from __future__ import annotations

import unittest
from typing import Any

import httpx

from mcp_proxmox.config import parse_config
from mcp_proxmox.pve.auth import PveAuthConfig, auth_config_from_app_config
from mcp_proxmox.pve.client import PveApiError, PveClient


def mock_handler(payload: dict[str, Any]) -> httpx.RequestHandler:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    return handler


def error_handler(status_code: int, body: str = "") -> httpx.RequestHandler:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, text=body)

    return handler


def valid_config(verify_ssl: bool = True) -> dict[str, object]:
    return {
        "connection": {
            "id": "local",
            "host": "https://pve.example.local:8006",
            "token_id": "root@pam!mcp-proxmox",
            "token_secret": "secret",
            "verify_ssl": verify_ssl,
        },
        "policy": {
            "mode": "READ_ONLY",
            "memory": {"allow_write": True},
        },
        "orchestrator": {
            "max_concurrent_per_node": 5,
            "max_concurrent_cluster": 15,
            "node_request_timeout_sec": 30,
            "aggregate_threshold": 500,
        },
    }


class PveClientTests(unittest.IsolatedAsyncioTestCase):
    def test_auth_config_is_built_from_app_config(self) -> None:
        config = parse_config(valid_config())
        auth = auth_config_from_app_config(config)

        self.assertEqual(auth.base_url, "https://pve.example.local:8006")
        self.assertEqual(auth.authorization_header, "PVEAPIToken=root@pam!mcp-proxmox=secret")
        self.assertEqual(auth.timeout_sec, 30.0)

    async def test_get_cluster_status_returns_typed_entries(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {"type": "cluster", "name": "pve", "version": 1},
                        {"type": "node", "name": "pve1", "online": 1},
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_cluster_status()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].type, "cluster")

    async def test_get_nodes_returns_typed_nodes(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {"node": "pve1", "status": "online", "cpu": 0.1},
                        {"node": "pve2", "status": "online", "cpu": 0.2},
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_nodes()

        self.assertEqual([node.node for node in result], ["pve1", "pve2"])

    async def test_get_node_returns_typed_status(self) -> None:
        payload = {"data": {"cpu": 0.5, "uptime": 123, "pveversion": "8.2"}}
        transport = httpx.MockTransport(mock_handler(payload))
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_node("pve1")

        self.assertEqual(result.cpu, 0.5)

    async def test_get_vms_returns_typed_resources(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {
                            "id": "qemu/100",
                            "node": "pve1",
                            "type": "qemu",
                            "vmid": 100,
                            "name": "web",
                            "status": "running",
                        },
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_vms()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "web")
        self.assertEqual(result[0].vmid, 100)

    async def test_get_vm_status_returns_typed_status(self) -> None:
        transport = httpx.MockTransport(
            mock_handler({"data": {"status": "running", "cpu": 0.15, "cpus": 2, "name": "web"}})
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_vm_status("pve1", 100)

        self.assertEqual(result.status, "running")
        self.assertEqual(result.cpu, 0.15)

    async def test_get_containers_returns_typed_resources(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {
                            "id": "lxc/300",
                            "node": "pve1",
                            "type": "lxc",
                            "vmid": 300,
                            "name": "ubuntu-ct",
                            "status": "running",
                        },
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_containers()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "ubuntu-ct")

    async def test_get_container_status_returns_typed_status(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {"data": {"status": "running", "cpu": 0.05, "cpus": 1, "name": "ubuntu-ct"}}
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_container_status("pve1", 300)

        self.assertEqual(result.status, "running")
        self.assertEqual(result.cpu, 0.05)

    async def test_get_storages_returns_typed_resources(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {
                            "id": "storage/local",
                            "node": "pve1",
                            "type": "storage",
                            "storage": "local",
                            "status": "available",
                        },
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_storages()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].storage, "local")

    async def test_get_storage_status_returns_typed_status(self) -> None:
        transport = httpx.MockTransport(
            mock_handler({"data": {"total": 1000, "used": 500, "used_fraction": 0.5, "active": 1}})
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_storage_status("pve1", "local")

        self.assertEqual(result.total, 1000)
        self.assertEqual(result.used_fraction, 0.5)

    async def test_get_network_interfaces_returns_typed(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {"iface": "vmbr0", "method": "static", "type": "bridge", "active": 1},
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_network_interfaces("pve1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].iface, "vmbr0")

    async def test_get_node_updates_returns_typed(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {
                            "title": "libc6",
                            "package": "libc6",
                            "version": "2.36-9",
                            "priority": "recommended",
                        },
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_node_updates("pve1")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].package, "libc6")

    async def test_get_vm_config_returns_config(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": {
                        "name": "web",
                        "vmid": 100,
                        "cores": 4,
                        "memory": 8192,
                        "sockets": 1,
                        "ostype": "l26",
                        "tags": "production;web",
                    }
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_vm_config("pve1", 100)

        self.assertEqual(result.name, "web")
        self.assertEqual(result.cores, 4)
        self.assertEqual(result.memory, 8192)

    async def test_get_container_config_returns_config(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": {
                        "hostname": "ubuntu-ct",
                        "vmid": 300,
                        "cores": 2,
                        "memory": 2048,
                        "ostype": "ubuntu",
                    }
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_container_config("pve1", 300)

        self.assertEqual(result.hostname, "ubuntu-ct")
        self.assertEqual(result.cores, 2)
        self.assertEqual(result.memory, 2048)

    async def test_get_storage_content_returns_items(self) -> None:
        transport = httpx.MockTransport(
            mock_handler(
                {
                    "data": [
                        {
                            "volid": "local:iso/ubuntu-24.04.iso",
                            "format": "iso",
                            "size": 4294967296,
                            "content": "iso",
                        },
                    ]
                }
            )
        )
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            result = await pve_client.get_storage_content("pve1", "local")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].volid, "local:iso/ubuntu-24.04.iso")
        self.assertEqual(result[0].format, "iso")

    async def test_http_error_raises_pve_api_error(self) -> None:
        transport = httpx.MockTransport(error_handler(500, '{"error":"boom"}'))
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)

            with self.assertRaises(PveApiError) as raised:
                await pve_client.get_nodes()

            self.assertEqual(raised.exception.status_code, 500)

    async def test_transport_error_raises_pve_api_error(self) -> None:
        def fail(_: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        transport = httpx.MockTransport(fail)
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)

            with self.assertRaises(PveApiError):
                await pve_client.get_nodes()

    async def test_missing_data_raises_pve_api_error(self) -> None:
        transport = httpx.MockTransport(mock_handler({"unexpected": []}))
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)

            with self.assertRaises(PveApiError):
                await pve_client.get_nodes()

    async def test_auth_header_is_sent(self) -> None:
        recorded: list[httpx.Request] = []

        def record(request: httpx.Request) -> httpx.Response:
            recorded.append(request)
            return httpx.Response(200, json={"data": []})

        transport = httpx.MockTransport(record)
        async with httpx.AsyncClient(transport=transport) as client:
            pve_client = PveClient(auth(), client=client)
            await pve_client.get_nodes()

        self.assertEqual(len(recorded), 1)
        self.assertEqual(
            recorded[0].headers.get("authorization"),
            "PVEAPIToken=root@pam!mcp-proxmox=secret",
        )


def auth(verify_ssl: bool = True) -> PveAuthConfig:
    return PveAuthConfig(
        base_url="https://pve.example.local:8006",
        token_id="root@pam!mcp-proxmox",
        token_secret="secret",
        verify_ssl=verify_ssl,
        timeout_sec=30.0,
    )


if __name__ == "__main__":
    unittest.main()
