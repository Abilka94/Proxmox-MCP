from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any

from mcp_proxmox.config import parse_config
from mcp_proxmox.mcp.handlers import MinimalMcpServer
from mcp_proxmox.mcp.registry import ALL_TOOLS, create_default_registry
from mcp_proxmox.policy import PolicyEngine


def valid_config() -> dict[str, object]:
    return {
        "connection": {
            "id": "local",
            "host": "https://pve.example.local:8006",
            "token_id": "root@pam!mcp-proxmox",
            "token_secret": "secret",
            "verify_ssl": True,
        },
        "policy": {
            "mode": "READ_ONLY",
            "memory": {"allow_write": True},
        },
    }


class MinimalMcpServerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        config = parse_config(valid_config())
        self.server = MinimalMcpServer(
            create_default_registry(config, FakePveClient()),
            PolicyEngine(config.policy),
        )

    async def test_initialize_returns_tools_capability(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2024-11-05"},
            }
        )

        assert response is not None
        self.assertEqual(response["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("tools", response["result"]["capabilities"])

    async def test_tools_list_returns_all_tools(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
            }
        )

        assert response is not None
        tools = response["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools], ALL_TOOLS)

    async def test_tools_call_returns_content(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "server_info", "arguments": {}},
            }
        )

        assert response is not None
        result = response["result"]
        self.assertEqual(result["content"][0]["type"], "text")
        payload = json.loads(result["content"][0]["text"])
        self.assertEqual(payload["server_name"], "mcp-proxmox")
        self.assertEqual(payload["available_tools"], ALL_TOOLS)

    async def test_cluster_info_returns_cluster_data(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "cluster_info", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["name"], "pve")
        self.assertEqual(payload["nodes"]["total"], 2)

    async def test_node_status_returns_node_details(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {"name": "node_status", "arguments": {"node_name": "pve1"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["cpu"], 0.25)

    async def test_node_status_requires_node_name(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {"name": "node_status", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_list_nodes_calls_domain_path(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 8,
                "method": "tools/call",
                "params": {"name": "list_nodes", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["nodes"][0]["node"], "pve1")

    # VM tools

    async def test_vm_list_returns_vms(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {"name": "vm_list", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["vms"][0]["name"], "web")

    async def test_vm_status_returns_details(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {"name": "vm_status", "arguments": {"node": "pve1", "vmid": 100}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["status"], "running")
        self.assertEqual(payload["cpu"], 0.15)

    async def test_vm_status_missing_params(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {"name": "vm_status", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_vm_config_returns_config(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {"name": "vm_config", "arguments": {"node": "pve1", "vmid": 100}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["name"], "web")
        self.assertEqual(payload["cores"], 4)

    async def test_vm_config_missing_params(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {"name": "vm_config", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    # Container tools

    async def test_container_list_returns_containers(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {"name": "container_list", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 2)

    async def test_container_status_returns_details(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {"name": "container_status", "arguments": {"node": "pve1", "vmid": 300}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["status"], "running")
        self.assertEqual(payload["cpu"], 0.05)

    async def test_container_status_missing_params(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 15,
                "method": "tools/call",
                "params": {"name": "container_status", "arguments": {"node": "pve1"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_container_config_returns_config(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 16,
                "method": "tools/call",
                "params": {"name": "container_config", "arguments": {"node": "pve1", "vmid": 300}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["hostname"], "ubuntu-ct")
        self.assertEqual(payload["cores"], 2)

    async def test_container_config_missing_params(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 17,
                "method": "tools/call",
                "params": {"name": "container_config", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    # Storage tools

    async def test_storage_list_returns_storages(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 16,
                "method": "tools/call",
                "params": {"name": "storage_list", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 2)

    async def test_storage_status_returns_details(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 17,
                "method": "tools/call",
                "params": {
                    "name": "storage_status",
                    "arguments": {"node": "pve1", "storage": "local"},
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["total"], 1000)

    async def test_storage_status_missing_params(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 18,
                "method": "tools/call",
                "params": {"name": "storage_status", "arguments": {"node": "pve1"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_storage_content_returns_items(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 19,
                "method": "tools/call",
                "params": {"name": "storage_content", "arguments": {"node": "pve1", "storage": "local"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["items"][0]["volid"], "local:iso/test.iso")

    async def test_storage_content_missing_params(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 20,
                "method": "tools/call",
                "params": {"name": "storage_content", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    # Network tools

    async def test_network_list_returns_interfaces(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 21,
                "method": "tools/call",
                "params": {"name": "network_list", "arguments": {"node": "pve1"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 2)

    async def test_network_list_missing_node(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 22,
                "method": "tools/call",
                "params": {"name": "network_list", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    # Task tools

    async def test_task_list_returns_tasks(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 26,
                "method": "tools/call",
                "params": {"name": "task_list", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 2)
        self.assertEqual(payload["tasks"][0]["upid"], "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:")

    async def test_task_list_with_filters(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 27,
                "method": "tools/call",
                "params": {
                    "name": "task_list",
                    "arguments": {
                        "node": "pve1",
                        "user": "root@pam",
                        "vmid": 100,
                        "type": "qemcreate",
                        "status": "running",
                        "limit": 10,
                    },
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("tasks", payload)

    async def test_task_status_returns_status(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 28,
                "method": "tools/call",
                "params": {
                    "name": "task_status",
                    "arguments": {"upid": "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:"},
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["status"], "stopped")
        self.assertEqual(payload["exitstatus"], "OK")

    async def test_task_status_missing_upid(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 29,
                "method": "tools/call",
                "params": {"name": "task_status", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_task_log_returns_lines(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {
                    "name": "task_log",
                    "arguments": {
                        "upid": "UPID:pve:00000001:00000001:00000001:vzdump:root@pam:",
                        "node": "pve1",
                    },
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["total_lines"], 2)
        self.assertEqual(payload["lines"][0]["text"], "starting backup")
        self.assertEqual(payload["lines"][1]["text"], " [...] 100%")

    async def test_task_log_missing_upid(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 31,
                "method": "tools/call",
                "params": {"name": "task_log", "arguments": {"node": "pve1"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_task_log_missing_node(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 32,
                "method": "tools/call",
                "params": {
                    "name": "task_log",
                    "arguments": {"upid": "UPID:pve:00000001:00000001:00000001:vzdump:root@pam:"},
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_task_wait_returns_status(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 33,
                "method": "tools/call",
                "params": {
                    "name": "task_wait",
                    "arguments": {"upid": "UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:"},
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["status"], "stopped")
        self.assertEqual(payload["exitstatus"], "OK")
        self.assertTrue(payload["completed"])

    async def test_task_wait_missing_upid(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 34,
                "method": "tools/call",
                "params": {"name": "task_wait", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_task_follow_returns_status_and_log(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 35,
                "method": "tools/call",
                "params": {
                    "name": "task_follow",
                    "arguments": {
                        "upid": "UPID:pve:00000001:00000001:00000001:vzdump:root@pam:",
                        "node": "pve1",
                    },
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["status"], "stopped")
        self.assertEqual(payload["exitstatus"], "OK")
        self.assertTrue(payload["completed"])
        self.assertIn("lines", payload)
        self.assertGreater(payload["total_lines"], 0)

    async def test_task_follow_missing_upid(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 36,
                "method": "tools/call",
                "params": {"name": "task_follow", "arguments": {"node": "pve1"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_task_follow_missing_node(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 37,
                "method": "tools/call",
                "params": {
                    "name": "task_follow",
                    "arguments": {"upid": "UPID:pve:00000001:00000001:00000001:vzdump:root@pam:"},
                },
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    # Update tools

    async def test_node_updates_returns_updates(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 23,
                "method": "tools/call",
                "params": {"name": "node_updates", "arguments": {"node": "pve1"}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["count"], 2)

    async def test_node_updates_missing_node(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 24,
                "method": "tools/call",
                "params": {"name": "node_updates", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertIn("error", payload)

    async def test_cluster_updates_aggregates(self) -> None:
        response = await self.server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 25,
                "method": "tools/call",
                "params": {"name": "cluster_updates", "arguments": {}},
            }
        )

        assert response is not None
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual(payload["total_count"], 2)
        self.assertEqual(payload["updates"][0]["node"], "pve1")


class McpProcessTests(unittest.TestCase):
    def test_module_process_handles_initialize_list_and_call(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root / "src")
        env["PVE_HOST"] = "https://pve.example.local:8006"
        env["PVE_TOKEN_ID"] = "root@pam!mcp-proxmox"
        env["PVE_TOKEN_SECRET"] = "secret"

        payload = b"".join(
            [
                frame(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {"protocolVersion": "2024-11-05"},
                    }
                ),
                frame({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                frame({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
                frame(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": "tools/call",
                        "params": {"name": "server_info", "arguments": {}},
                    }
                ),
            ]
        )

        process = subprocess.run(
            [sys.executable, "-m", "mcp_proxmox"],
            input=payload,
            capture_output=True,
            cwd=repo_root,
            env=env,
            check=False,
            timeout=10,
        )

        self.assertEqual(process.returncode, 0, process.stderr.decode("utf-8", errors="replace"))

        responses = parse_frames(process.stdout)
        self.assertEqual(len(responses), 3)
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "mcp-proxmox")
        tool_names = [tool["name"] for tool in responses[1]["result"]["tools"]]
        self.assertEqual(tool_names, ALL_TOOLS)
        content = json.loads(responses[2]["result"]["content"][0]["text"])
        self.assertEqual(content["available_tools"], ALL_TOOLS)


class FakeNode:
    def __init__(self, node: str, status: str) -> None:
        self.node = node
        self.status = status

    def model_dump(self, mode: str = "json") -> dict[str, str]:
        return {"node": self.node, "status": self.status}


class FakeClusterStatusEntry:
    def __init__(
        self,
        type: str,
        name: str | None = None,
        online: int | None = None,
        version: int | None = None,
        quorate: int | None = None,
    ) -> None:
        self.type = type
        self.name = name
        self.online = online
        self.version = version
        self.quorate = quorate

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        d: dict[str, object] = {"type": self.type}
        if self.name is not None:
            d["name"] = self.name
        if self.online is not None:
            d["online"] = self.online
        if self.version is not None:
            d["version"] = self.version
        if self.quorate is not None:
            d["quorate"] = self.quorate
        return d


class FakeNodeStatus:
    def __init__(
        self,
        cpu: float | None = None,
        uptime: int | None = None,
        pveversion: str | None = None,
    ) -> None:
        self.cpu = cpu
        self.uptime = uptime
        self.pveversion = pveversion

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        d: dict[str, object] = {}
        if self.cpu is not None:
            d["cpu"] = self.cpu
        if self.uptime is not None:
            d["uptime"] = self.uptime
        if self.pveversion is not None:
            d["pveversion"] = self.pveversion
        return d


class FakeVmResource:
    def __init__(
        self,
        id: str,
        node: str,
        type: str,
        vmid: int,
        name: str | None = None,
        status: str | None = None,
    ) -> None:
        self.id = id
        self.node = node
        self.type = type
        self.vmid = vmid
        self.name = name
        self.status = status

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        return {
            "id": self.id,
            "node": self.node,
            "type": self.type,
            "vmid": self.vmid,
            "name": self.name,
            "status": self.status,
        }


class FakeVmStatus:
    def __init__(self, status: str, cpu: float, name: str | None = None) -> None:
        self.status = status
        self.cpu = cpu
        self.name = name

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        d: dict[str, object] = {"status": self.status, "cpu": self.cpu}
        if self.name is not None:
            d["name"] = self.name
        return d


class FakeVmConfig:
    def __init__(self, name: str, cores: int, memory: int) -> None:
        self.name = name
        self.cores = cores
        self.memory = memory

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        return {"name": self.name, "cores": self.cores, "memory": self.memory}


class FakeLxcResource:
    def __init__(
        self,
        id: str,
        node: str,
        type: str,
        vmid: int,
        name: str | None = None,
        status: str | None = None,
    ) -> None:
        self.id = id
        self.node = node
        self.type = type
        self.vmid = vmid
        self.name = name
        self.status = status

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        return {
            "id": self.id,
            "node": self.node,
            "type": self.type,
            "vmid": self.vmid,
            "name": self.name,
            "status": self.status,
        }


class FakeLxcStatus:
    def __init__(self, status: str, cpu: float, name: str | None = None) -> None:
        self.status = status
        self.cpu = cpu
        self.name = name

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        d: dict[str, object] = {"status": self.status, "cpu": self.cpu}
        if self.name is not None:
            d["name"] = self.name
        return d


class FakeLxcConfig:
    def __init__(self, hostname: str, cores: int, memory: int) -> None:
        self.hostname = hostname
        self.cores = cores
        self.memory = memory

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        return {"hostname": self.hostname, "cores": self.cores, "memory": self.memory}


class FakeStorageResource:
    def __init__(self, storage: str) -> None:
        self.storage = storage

    def model_dump(self, mode: str = "json") -> dict[str, str]:
        return {"storage": self.storage}


class FakeStorageStatus:
    def __init__(self, total: int) -> None:
        self.total = total

    def model_dump(self, mode: str = "json") -> dict[str, int]:
        return {"total": self.total}


class FakeStorageContentItem:
    def __init__(self, volid: str, format: str) -> None:
        self.volid = volid
        self.format = format

    def model_dump(self, mode: str = "json") -> dict[str, str]:
        return {"volid": self.volid, "format": self.format}


class FakeNetworkInterface:
    def __init__(self, iface: str) -> None:
        self.iface = iface

    def model_dump(self, mode: str = "json") -> dict[str, str]:
        return {"iface": self.iface}


class FakeNodeUpdateEntry:
    def __init__(self, title: str) -> None:
        self.title = title

    def model_dump(self, mode: str = "json") -> dict[str, str]:
        return {"title": self.title}


class FakeClusterUpdateEntry:
    def __init__(self, node: str, title: str) -> None:
        self.node = node
        self.title = title

    def model_dump(self, mode: str = "json") -> dict[str, str]:
        return {"node": self.node, "title": self.title}


class FakePveClient:
    async def get_nodes(self) -> list[FakeNode]:
        return [FakeNode("pve1", "online"), FakeNode("pve2", "online")]

    async def get_cluster_status(self) -> list[FakeClusterStatusEntry]:
        return [
            FakeClusterStatusEntry(type="cluster", name="pve", version=1, quorate=1),
            FakeClusterStatusEntry(type="node", name="pve1", online=1),
            FakeClusterStatusEntry(type="node", name="pve2", online=1),
        ]

    async def get_node(self, node_name: str) -> FakeNodeStatus:
        return FakeNodeStatus(cpu=0.25, uptime=12345, pveversion="8.2.4")

    async def get_vms(self) -> list[FakeVmResource]:
        return [
            FakeVmResource(
                id="qemu/100", node="pve1", type="qemu", vmid=100, name="web", status="running"
            ),
            FakeVmResource(
                id="qemu/101", node="pve1", type="qemu", vmid=101, name="db", status="stopped"
            ),
        ]

    async def get_vm_status(self, node: str, vmid: int) -> FakeVmStatus:
        return FakeVmStatus(status="running", cpu=0.15, name="web")

    async def get_vm_config(self, node: str, vmid: int) -> FakeVmConfig:
        return FakeVmConfig(name="web", cores=4, memory=8192)

    async def get_containers(self) -> list[FakeLxcResource]:
        return [
            FakeLxcResource(
                id="lxc/300", node="pve1", type="lxc", vmid=300, name="ubuntu-ct", status="running"
            ),
            FakeLxcResource(
                id="lxc/301", node="pve2", type="lxc", vmid=301, name="debian-ct", status="stopped"
            ),
        ]

    async def get_container_status(self, node: str, vmid: int) -> FakeLxcStatus:
        return FakeLxcStatus(status="running", cpu=0.05, name="ubuntu-ct")

    async def get_container_config(self, node: str, vmid: int) -> FakeLxcConfig:
        return FakeLxcConfig(hostname="ubuntu-ct", cores=2, memory=2048)

    async def get_storages(self) -> list[FakeStorageResource]:
        return [FakeStorageResource("local"), FakeStorageResource("nfs-backup")]

    async def get_storage_status(self, node: str, storage: str) -> FakeStorageStatus:
        return FakeStorageStatus(total=1000)

    async def get_storage_content(self, node: str, storage: str) -> list[FakeStorageContentItem]:
        return [FakeStorageContentItem("local:iso/test.iso", "iso")]

    async def get_network_interfaces(self, node: str) -> list[FakeNetworkInterface]:
        return [FakeNetworkInterface("vmbr0"), FakeNetworkInterface("enp1s0")]

    async def get_node_updates(self, node: str) -> list[FakeNodeUpdateEntry]:
        return [FakeNodeUpdateEntry("libc6"), FakeNodeUpdateEntry("openssl")]

    async def get_cluster_updates(self) -> list[FakeClusterUpdateEntry]:
        return [
            FakeClusterUpdateEntry("pve1", "libc6"),
            FakeClusterUpdateEntry("pve2", "openssl"),
        ]

    async def get_tasks(self, **kwargs) -> list[FakeTaskListEntry]:
        return [
            FakeTaskListEntry(
                upid="UPID:pve:00000001:00000001:00000001:qemcreate:root@pam:",
                node="pve1",
                user="root@pam",
                type="qemcreate",
                status="stopped",
                exitstatus="OK",
            ),
            FakeTaskListEntry(
                upid="UPID:pve:00000002:00000002:00000002:vzdump:root@pam:",
                node="pve1",
                user="root@pam",
                type="vzdump",
                status="running",
            ),
        ]

    async def get_task_status(self, upid: str, **kwargs) -> FakeTaskStatus:
        return FakeTaskStatus(status="stopped", exitstatus="OK")

    async def get_task_log(self, node: str, upid: str, **kwargs) -> list[FakeTaskLogEntry]:
        return [
            FakeTaskLogEntry(t="starting backup"),
            FakeTaskLogEntry(t=" [...] 100%", n=42),
        ]


class FakeTaskListEntry:
    def __init__(
        self,
        upid: str,
        node: str | None = None,
        user: str | None = None,
        type: str | None = None,
        status: str | None = None,
        exitstatus: str | None = None,
        starttime: int | None = None,
        endtime: int | None = None,
        id: str | None = None,
    ) -> None:
        self.upid = upid
        self.node = node
        self.user = user
        self.type = type
        self.status = status
        self.exitstatus = exitstatus
        self.starttime = starttime
        self.endtime = endtime
        self.id = id

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        d: dict[str, object] = {"upid": self.upid}
        if self.node is not None:
            d["node"] = self.node
        if self.user is not None:
            d["user"] = self.user
        if self.type is not None:
            d["type"] = self.type
        if self.status is not None:
            d["status"] = self.status
        if self.exitstatus is not None:
            d["exitstatus"] = self.exitstatus
        if self.starttime is not None:
            d["starttime"] = self.starttime
        if self.endtime is not None:
            d["endtime"] = self.endtime
        if self.id is not None:
            d["id"] = self.id
        return d


class FakeTaskStatus:
    def __init__(self, status: str, exitstatus: str | None = None) -> None:
        self.status = status
        self.exitstatus = exitstatus

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        d: dict[str, object] = {"status": self.status}
        if self.exitstatus is not None:
            d["exitstatus"] = self.exitstatus
        return d


class FakeTaskLogEntry:
    def __init__(self, t: str, n: int | None = None) -> None:
        self.t = t
        self.n = n

    def model_dump(self, mode: str = "json") -> dict[str, object]:
        d: dict[str, object] = {"t": self.t}
        if self.n is not None:
            d["n"] = self.n
        return d


def frame(message: dict[str, Any]) -> bytes:
    body = json.dumps(message).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def parse_frames(stream: bytes) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    cursor = 0

    while cursor < len(stream):
        header_end = stream.index(b"\r\n\r\n", cursor)
        headers = stream[cursor:header_end].decode("ascii").split("\r\n")
        cursor = header_end + 4

        content_length = 0
        for header in headers:
            name, _, value = header.partition(":")
            if name.lower() == "content-length":
                content_length = int(value.strip())
                break

        body = stream[cursor : cursor + content_length]
        cursor += content_length
        messages.append(json.loads(body.decode("utf-8")))

    return messages


if __name__ == "__main__":
    unittest.main()
