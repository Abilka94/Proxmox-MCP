"""Minimal MCP tool registry for Phase 1A bootstrap."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from mcp_proxmox.config.models import AppConfig
from mcp_proxmox.domains.cluster import cluster_info
from mcp_proxmox.domains.containers import container_config, container_list, container_status
from mcp_proxmox.domains.network import network_list
from mcp_proxmox.domains.nodes import list_nodes, node_status
from mcp_proxmox.domains.storage import storage_content, storage_list, storage_status
from mcp_proxmox.domains.tasks import task_list, task_log, task_status
from mcp_proxmox.domains.updates import cluster_updates, node_updates
from mcp_proxmox.domains.vms import vm_config, vm_list, vm_status
from mcp_proxmox.policy import ToolPolicy, ToolTier
from mcp_proxmox.pve.client import PveClient

ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]

ALL_TOOLS = [
    "server_info",
    "list_nodes",
    "cluster_info",
    "node_status",
    "vm_list",
    "vm_status",
    "vm_config",
    "container_list",
    "container_status",
    "container_config",
    "storage_list",
    "storage_status",
    "storage_content",
    "network_list",
    "node_updates",
    "cluster_updates",
    "task_list",
    "task_status",
    "task_log",
]


@dataclass(frozen=True)
class ToolDefinition:
    """Static metadata and handler for a tool."""

    name: str
    description: str
    input_schema: dict[str, Any]
    policy: ToolPolicy
    handler: ToolHandler

    def descriptor(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


class ToolRegistry:
    """In-memory registry for MCP tools."""

    def __init__(self, tools: list[ToolDefinition]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)


def create_default_registry(config: AppConfig, pve_client: PveClient | None = None) -> ToolRegistry:
    """Create the minimal T-104 registry."""

    if pve_client is None:
        raise RuntimeError("PVE client is required for tool registry")

    async def server_info_tool(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "server_name": "mcp-proxmox",
            "server_version": "0.1.0-alpha.0",
            "transport": "stdio",
            "policy_mode": config.policy.mode.value,
            "connection_id": config.connection.id,
            "available_tools": ALL_TOOLS,
        }

    async def list_nodes_tool(_: dict[str, Any]) -> dict[str, Any]:
        return await list_nodes(pve_client)

    async def cluster_info_tool(_: dict[str, Any]) -> dict[str, Any]:
        return await cluster_info(pve_client)

    async def node_status_tool(params: dict[str, Any]) -> dict[str, Any]:
        node_name = params.get("node_name")
        if not isinstance(node_name, str) or not node_name:
            return {"error": "node_name is required"}
        return await node_status(pve_client, node_name)

    async def vm_list_tool(_: dict[str, Any]) -> dict[str, Any]:
        return await vm_list(pve_client)

    async def vm_status_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        vmid = params.get("vmid")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        if not isinstance(vmid, int):
            return {"error": "vmid is required and must be an integer"}
        return await vm_status(pve_client, node, vmid)

    async def vm_config_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        vmid = params.get("vmid")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        if not isinstance(vmid, int):
            return {"error": "vmid is required and must be an integer"}
        return await vm_config(pve_client, node, vmid)

    async def container_list_tool(_: dict[str, Any]) -> dict[str, Any]:
        return await container_list(pve_client)

    async def container_status_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        vmid = params.get("vmid")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        if not isinstance(vmid, int):
            return {"error": "vmid is required and must be an integer"}
        return await container_status(pve_client, node, vmid)

    async def container_config_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        vmid = params.get("vmid")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        if not isinstance(vmid, int):
            return {"error": "vmid is required and must be an integer"}
        return await container_config(pve_client, node, vmid)

    async def storage_list_tool(_: dict[str, Any]) -> dict[str, Any]:
        return await storage_list(pve_client)

    async def storage_status_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        storage = params.get("storage")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        if not isinstance(storage, str) or not storage:
            return {"error": "storage is required"}
        return await storage_status(pve_client, node, storage)

    async def storage_content_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        storage = params.get("storage")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        if not isinstance(storage, str) or not storage:
            return {"error": "storage is required"}
        return await storage_content(pve_client, node, storage)

    async def network_list_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        return await network_list(pve_client, node)

    async def node_updates_tool(params: dict[str, Any]) -> dict[str, Any]:
        node = params.get("node")
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        return await node_updates(pve_client, node)

    async def cluster_updates_tool(_: dict[str, Any]) -> dict[str, Any]:
        return await cluster_updates(pve_client)

    async def task_list_tool(params: dict[str, Any]) -> dict[str, Any]:
        return await task_list(
            pve_client,
            node=params.get("node"),
            user=params.get("user"),
            vmid=params.get("vmid"),
            type_filter=params.get("type"),
            status=params.get("status"),
            limit=params.get("limit", 50),
        )

    async def task_status_tool(params: dict[str, Any]) -> dict[str, Any]:
        upid = params.get("upid")
        if not isinstance(upid, str) or not upid:
            return {"error": "upid is required"}
        return await task_status(
            pve_client,
            upid,
            node=params.get("node"),
        )

    async def task_log_tool(params: dict[str, Any]) -> dict[str, Any]:
        upid = params.get("upid")
        node = params.get("node")
        if not isinstance(upid, str) or not upid:
            return {"error": "upid is required"}
        if not isinstance(node, str) or not node:
            return {"error": "node is required"}
        return await task_log(
            pve_client,
            upid,
            node,
            start=params.get("start"),
        )

    return ToolRegistry(
        [
            ToolDefinition(
                name="server_info",
                description="Return basic MCP-Proxmox server information.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="server_info", tier=ToolTier.READ),
                handler=server_info_tool,
            ),
            ToolDefinition(
                name="list_nodes",
                description="List Proxmox VE nodes from the connected cluster.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="list_nodes", tier=ToolTier.READ),
                handler=list_nodes_tool,
            ),
            ToolDefinition(
                name="cluster_info",
                description="Return cluster information with node status summary.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="cluster_info", tier=ToolTier.READ),
                handler=cluster_info_tool,
            ),
            ToolDefinition(
                name="node_status",
                description="Return detailed status for a specific Proxmox node.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node_name": {
                            "type": "string",
                            "description": "Name of the node (e.g. pve1)",
                        }
                    },
                    "required": ["node_name"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="node_status", tier=ToolTier.READ),
                handler=node_status_tool,
            ),
            ToolDefinition(
                name="vm_list",
                description="List all QEMU VMs in the cluster.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="vm_list", tier=ToolTier.READ),
                handler=vm_list_tool,
            ),
            ToolDefinition(
                name="vm_status",
                description="Return detailed status for a specific VM.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                        "vmid": {"type": "integer", "description": "VM ID"},
                    },
                    "required": ["node", "vmid"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="vm_status", tier=ToolTier.READ),
                handler=vm_status_tool,
            ),
            ToolDefinition(
                name="vm_config",
                description="Return full configuration for a specific VM.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                        "vmid": {"type": "integer", "description": "VM ID"},
                    },
                    "required": ["node", "vmid"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="vm_config", tier=ToolTier.READ),
                handler=vm_config_tool,
            ),
            ToolDefinition(
                name="container_list",
                description="List all LXC containers in the cluster.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="container_list", tier=ToolTier.READ),
                handler=container_list_tool,
            ),
            ToolDefinition(
                name="container_status",
                description="Return detailed status for a specific container.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                        "vmid": {"type": "integer", "description": "Container ID"},
                    },
                    "required": ["node", "vmid"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="container_status", tier=ToolTier.READ),
                handler=container_status_tool,
            ),
            ToolDefinition(
                name="container_config",
                description="Return full configuration for a specific container.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                        "vmid": {"type": "integer", "description": "Container ID"},
                    },
                    "required": ["node", "vmid"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="container_config", tier=ToolTier.READ),
                handler=container_config_tool,
            ),
            ToolDefinition(
                name="storage_list",
                description="List all storage resources in the cluster.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="storage_list", tier=ToolTier.READ),
                handler=storage_list_tool,
            ),
            ToolDefinition(
                name="storage_status",
                description="Return detailed status for a specific storage.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                        "storage": {"type": "string", "description": "Storage ID"},
                    },
                    "required": ["node", "storage"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="storage_status", tier=ToolTier.READ),
                handler=storage_status_tool,
            ),
            ToolDefinition(
                name="storage_content",
                description="List content (ISOs, templates, backups) on a specific storage.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                        "storage": {"type": "string", "description": "Storage ID"},
                    },
                    "required": ["node", "storage"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="storage_content", tier=ToolTier.READ),
                handler=storage_content_tool,
            ),
            ToolDefinition(
                name="network_list",
                description="List network interfaces on a specific node.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                    },
                    "required": ["node"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="network_list", tier=ToolTier.READ),
                handler=network_list_tool,
            ),
            ToolDefinition(
                name="node_updates",
                description="List available APT updates on a specific node.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {"type": "string", "description": "Node name"},
                    },
                    "required": ["node"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="node_updates", tier=ToolTier.READ),
                handler=node_updates_tool,
            ),
            ToolDefinition(
                name="cluster_updates",
                description="List available APT updates across all nodes in the cluster.",
                input_schema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="cluster_updates", tier=ToolTier.READ),
                handler=cluster_updates_tool,
            ),
            ToolDefinition(
                name="task_list",
                description="List recent tasks across the cluster with optional filters.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Filter by node name",
                        },
                        "user": {
                            "type": "string",
                            "description": "Filter by user who initiated the task",
                        },
                        "vmid": {
                            "type": "integer",
                            "description": "Filter by VM/container ID",
                        },
                        "type": {
                            "type": "string",
                            "description": "Filter by task type (e.g. qemcreate, vzdump)",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by status (running, stopped)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return (default 50, max 500)",
                        },
                    },
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="task_list", tier=ToolTier.READ),
                handler=task_list_tool,
            ),
            ToolDefinition(
                name="task_status",
                description="Return status for a specific task by UPID.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "upid": {
                            "type": "string",
                            "description": "UPID of the task",
                        },
                        "node": {
                            "type": "string",
                            "description": "Node name (fallback for cross-node UPID)",
                        },
                    },
                    "required": ["upid"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="task_status", tier=ToolTier.READ),
                handler=task_status_tool,
            ),
            ToolDefinition(
                name="task_log",
                description="Return log lines for a specific task.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "upid": {
                            "type": "string",
                            "description": "UPID of the task",
                        },
                        "node": {
                            "type": "string",
                            "description": "Node name where the task runs",
                        },
                        "start": {
                            "type": "integer",
                            "description": "Starting line number (0-indexed)",
                        },
                    },
                    "required": ["upid", "node"],
                    "additionalProperties": False,
                },
                policy=ToolPolicy(name="task_log", tier=ToolTier.READ),
                handler=task_log_tool,
            ),
        ]
    )
