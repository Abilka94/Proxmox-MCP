"""Async HTTP client for the Proxmox VE API using httpx."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from mcp_proxmox.logging import get_logger
from mcp_proxmox.pve.auth.config import PveAuthConfig
from mcp_proxmox.pve.models.responses import (
    ClusterStatusEntry,
    ClusterUpdateEntry,
    LxcConfig,
    LxcResource,
    LxcStatus,
    NetworkInterface,
    NodeInfo,
    NodeStatus,
    NodeUpdateEntry,
    StorageContentItem,
    StorageResource,
    StorageStatus,
    VmConfig,
    VmResource,
    VmStatus,
)


@dataclass(frozen=True)
class PveApiError(RuntimeError):
    """Structured PVE client error."""

    message: str
    path: str
    status_code: int | None = None
    details: str | None = None

    def __str__(self) -> str:
        if self.status_code is None:
            return f"{self.message} ({self.path})"
        return f"{self.message} ({self.status_code} {self.path})"


class PveClient:
    """Small async PVE API client for Phase 1A read operations."""

    def __init__(
        self,
        auth: PveAuthConfig,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._auth = auth
        self._client = client
        self._logger = get_logger("mcp_proxmox.pve.client")

    async def get_cluster_status(self) -> list[ClusterStatusEntry]:
        payload = await self._get_json("/cluster/status")
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for cluster status", "/cluster/status")
        return [ClusterStatusEntry.model_validate(item) for item in payload]

    async def get_nodes(self) -> list[NodeInfo]:
        payload = await self._get_json("/nodes")
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for nodes", "/nodes")
        return [NodeInfo.model_validate(item) for item in payload]

    async def get_node(self, node_name: str) -> NodeStatus:
        path = f"/nodes/{httpx.URL(node_name).path}/status"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for node status", path)
        return NodeStatus.model_validate(payload)

    async def get_vms(self) -> list[VmResource]:
        payload = await self._get_json("/cluster/resources?type=vm")
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for VMs", "/cluster/resources")
        return [VmResource.model_validate(item) for item in payload]

    async def get_vm_status(self, node: str, vmid: int) -> VmStatus:
        path = f"/nodes/{httpx.URL(node).path}/qemu/{vmid}/status/current"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for VM status", path)
        return VmStatus.model_validate(payload)

    async def get_containers(self) -> list[LxcResource]:
        payload = await self._get_json("/cluster/resources?type=vm")
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for containers", "/cluster/resources")
        lxc_items = [item for item in payload if item.get("type") == "lxc"]
        return [LxcResource.model_validate(item) for item in lxc_items]

    async def get_container_status(self, node: str, vmid: int) -> LxcStatus:
        path = f"/nodes/{httpx.URL(node).path}/lxc/{vmid}/status/current"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for container status", path)
        return LxcStatus.model_validate(payload)

    async def get_storages(self) -> list[StorageResource]:
        payload = await self._get_json("/cluster/resources?type=storage")
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for storage", "/cluster/resources")
        return [StorageResource.model_validate(item) for item in payload]

    async def get_storage_status(self, node: str, storage: str) -> StorageStatus:
        path = f"/nodes/{httpx.URL(node).path}/storage/{httpx.URL(storage).path}/status"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for storage status", path)
        return StorageStatus.model_validate(payload)

    async def get_network_interfaces(self, node: str) -> list[NetworkInterface]:
        path = f"/nodes/{httpx.URL(node).path}/network"
        payload = await self._get_json(path)
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for network", path)
        return [NetworkInterface.model_validate(item) for item in payload]

    async def get_vm_config(self, node: str, vmid: int) -> VmConfig:
        path = f"/nodes/{httpx.URL(node).path}/qemu/{vmid}/config"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for VM config", path)
        return VmConfig.model_validate(payload)

    async def get_container_config(self, node: str, vmid: int) -> LxcConfig:
        path = f"/nodes/{httpx.URL(node).path}/lxc/{vmid}/config"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for container config", path)
        return LxcConfig.model_validate(payload)

    async def get_storage_content(self, node: str, storage: str) -> list[StorageContentItem]:
        path = f"/nodes/{httpx.URL(node).path}/storage/{httpx.URL(storage).path}/content"
        payload = await self._get_json(path)
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for storage content", path)
        return [StorageContentItem.model_validate(item) for item in payload]

    async def get_cluster_updates(self) -> list[ClusterUpdateEntry]:
        nodes = await self.get_nodes()
        results: list[ClusterUpdateEntry] = []
        for node_info in nodes:
            node_name = node_info.node
            try:
                updates = await self.get_node_updates(node_name)
                for update in updates:
                    results.append(
                        ClusterUpdateEntry(
                            node=node_name,
                            title=update.title,
                            package=update.package,
                            version=update.version,
                            old_version=update.old_version,
                            arch=update.arch,
                            description=update.description,
                            priority=update.priority,
                        )
                    )
            except PveApiError:
                results.append(
                    ClusterUpdateEntry(
                        node=node_name,
                        title="<failed to fetch updates>",
                    )
                )
        return results

    async def get_node_updates(self, node: str) -> list[NodeUpdateEntry]:
        path = f"/nodes/{httpx.URL(node).path}/apt/update"
        payload = await self._get_json(path)
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for updates", path)
        return [NodeUpdateEntry.model_validate(item) for item in payload]

    async def _get_json(self, path: str) -> Any:
        url = f"{self._auth.base_url}/api2/json{path}"

        try:
            client = self._client or self._make_client()
            response = await client.get(
                url,
                headers={
                    "Accept": "application/json",
                    "Authorization": self._auth.authorization_header,
                },
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            details = exc.response.text
            raise PveApiError(
                "PVE API request failed", path, exc.response.status_code, details
            ) from exc
        except httpx.RequestError as exc:
            raise PveApiError("PVE API transport error", path, details=str(exc)) from exc
        except httpx.TimeoutException as exc:
            raise PveApiError("PVE API request timed out", path) from exc

        if not isinstance(body, dict) or "data" not in body:
            raise PveApiError("PVE API response is missing data", path)

        self._logger.info("pve_get", extra={"path": path, "outcome": "ok"})
        return body["data"]

    def _make_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            verify=self._auth.verify_ssl,
            timeout=httpx.Timeout(self._auth.timeout_sec),
        )
