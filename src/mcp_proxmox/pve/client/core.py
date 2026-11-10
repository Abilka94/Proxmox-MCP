"""Async HTTP client for the Proxmox VE API using httpx."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import ValidationError

from mcp_proxmox.logging import get_logger
from mcp_proxmox.pve.auth.config import PveAuthConfig
from mcp_proxmox.pve.client.task_validation import validate_task_identity
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
    TaskListEntry,
    TaskLogEntry,
    TaskStatus,
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
    kind: str | None = None
    request_outcome: str | None = None

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

    async def get_tasks(
        self,
        *,
        node: str | None = None,
        user: str | None = None,
        vmid: int | None = None,
        type_filter: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[TaskListEntry]:
        if node is not None:
            path = f"/nodes/{httpx.URL(node).path}/tasks"
            params: dict[str, Any] = {"limit": limit}
        else:
            path = "/cluster/tasks"
            params = {}

        payload = await self._get_json(path, params=params)
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for tasks", path)
        entries = [TaskListEntry.model_validate(item) for item in payload]

        filtered = entries
        if user is not None:
            filtered = [e for e in filtered if e.user == user]
        if vmid is not None:
            filtered = [e for e in filtered if e.vmid == vmid]
        if type_filter is not None:
            filtered = [e for e in filtered if e.type == type_filter]
        if status is not None:
            filtered = [e for e in filtered if e.status == status]

        return filtered[:limit]

    async def get_task_status(self, upid: str, *, node: str | None = None) -> TaskStatus:
        try:
            return await self._get_task_status_cluster(upid)
        except PveApiError as exc:
            if exc.status_code in (400, 501) and node:
                return await self._get_task_status_node(node, upid)
            raise

    async def _get_task_status_cluster(self, upid: str) -> TaskStatus:
        path = f"/cluster/tasks/{urllib.parse.quote(upid, safe='')}/status"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for task status", path)
        return TaskStatus.model_validate(payload)

    async def _get_task_status_node(self, node: str, upid: str) -> TaskStatus:
        path = f"/nodes/{httpx.URL(node).path}/tasks/{urllib.parse.quote(upid, safe='')}/status"
        payload = await self._get_json(path)
        if not isinstance(payload, dict):
            raise PveApiError("Expected object response for task status", path)
        return TaskStatus.model_validate(payload)

    async def get_task_log(
        self, node: str, upid: str, *, start: int | None = None
    ) -> list[TaskLogEntry]:
        path = f"/nodes/{httpx.URL(node).path}/tasks/{urllib.parse.quote(upid, safe='')}/log"
        params: dict[str, Any] = {}
        if start is not None:
            params["start"] = start

        payload = await self._get_json(path, params=params)
        if not isinstance(payload, list):
            raise PveApiError("Expected list response for task log", path)
        return [TaskLogEntry.model_validate(item) for item in payload]

    async def get_task_status_on_node(self, node: str, upid: str) -> TaskStatus:
        """Нодальное наблюдение без cluster fallback для mutate-контракта."""
        validate_task_identity(node, upid)
        if self._client is None:
            async with self._make_client() as client:
                return await PveClient(self._auth, client=client).get_task_status_on_node(
                    node, upid
                )
        path = (
            f"/nodes/{urllib.parse.quote(node, safe='')}/tasks/"
            f"{urllib.parse.quote(upid, safe='')}/status"
        )
        try:
            response = await self._client.get(
                f"{self._auth.base_url}/api2/json{path}",
                headers={
                    "Accept": "application/json",
                    "Authorization": self._auth.authorization_header,
                },
                follow_redirects=False,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            kind = {
                401: "authentication_failed",
                403: "permission_denied",
                404: "resource_not_found",
                501: "endpoint_unsupported",
            }.get(code, "api_error")
            raise PveApiError("Ошибка HTTP при чтении статуса", path, code, kind=kind) from exc
        except httpx.RequestError as exc:
            raise PveApiError(
                "Ошибка транспорта при чтении статуса", path, kind="transport_error"
            ) from exc
        try:
            body = response.json()
            if not isinstance(body, dict) or not isinstance(body.get("data"), dict):
                raise ValueError("invalid status envelope")
            result = TaskStatus.model_validate(body["data"])
            if result.status not in ("running", "stopped"):
                raise ValueError("invalid status")
        except (ValueError, ValidationError) as exc:
            raise PveApiError(
                "Некорректный ответ статуса задачи",
                path,
                response.status_code,
                kind="invalid_response",
            ) from exc
        return result

    async def stop_task(self, node: str, upid: str) -> None:
        validate_task_identity(node, upid)
        path = (
            f"/nodes/{urllib.parse.quote(node, safe='')}/tasks/{urllib.parse.quote(upid, safe='')}"
        )
        await self._delete_json(path, require_null=True)

    async def _delete_json(self, path: str, *, require_null: bool = False) -> Any:
        if self._client is not None:
            return await self._send_delete(self._client, path, require_null=require_null)
        async with self._make_client() as client:
            return await self._send_delete(client, path, require_null=require_null)

    async def _send_delete(
        self, client: httpx.AsyncClient, path: str, *, require_null: bool = False
    ) -> Any:
        response: httpx.Response | None = None
        outcome = "unknown"
        kind: str | None = None
        try:
            try:
                response = await client.delete(
                    f"{self._auth.base_url}/api2/json{path}",
                    headers={
                        "Accept": "application/json",
                        "Authorization": self._auth.authorization_header,
                    },
                    follow_redirects=False,
                )
                response.raise_for_status()
                body = response.json()
                if not isinstance(body, dict) or "data" not in body:
                    raise ValueError("invalid DELETE envelope")
                if require_null and body["data"] is not None:
                    raise ValueError("invalid DELETE acknowledgement")
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                kind = {
                    400: "invalid_request",
                    401: "authentication_failed",
                    403: "permission_denied",
                    404: "resource_not_found",
                    501: "endpoint_unsupported",
                }.get(code, "http_error")
                outcome = "rejected" if 400 <= code < 500 or code == 501 else "unknown"
                raise PveApiError(
                    "Ошибка HTTP при DELETE", path, code, kind=kind, request_outcome=outcome
                ) from exc
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
                outcome, kind = "not_sent", "transport_not_sent"
                raise PveApiError(
                    "DELETE не отправлен", path, kind=kind, request_outcome=outcome
                ) from exc
            except httpx.RequestError as exc:
                kind = "transport_error"
                raise PveApiError(
                    "Исход DELETE неизвестен", path, kind=kind, request_outcome=outcome
                ) from exc
            except ValueError as exc:
                kind = "invalid_response"
                raise PveApiError(
                    "Некорректный ответ DELETE",
                    path,
                    response.status_code if response is not None else None,
                    kind=kind,
                    request_outcome=outcome,
                ) from exc
            outcome = "accepted"
            return body["data"]
        finally:
            self._logger.info(
                "pve_delete",
                extra={
                    "phase": "delete",
                    "request_outcome": outcome,
                    "http_status": response.status_code if response is not None else None,
                    "kind": kind,
                },
            )

    async def _post_json(self, path: str, data: dict[str, Any] | None = None) -> Any:
        if self._client is not None:
            return await self._send_post(self._client, path, data)
        async with self._make_client() as client:
            return await self._send_post(client, path, data)

    async def _send_post(
        self,
        client: httpx.AsyncClient,
        path: str,
        data: dict[str, Any] | None,
    ) -> Any:
        url = f"{self._auth.base_url}/api2/json{path}"

        try:
            response = await client.post(
                url,
                headers={
                    "Accept": "application/json",
                    "Authorization": self._auth.authorization_header,
                },
                data=data,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            details = exc.response.text
            raise PveApiError(
                "PVE API request failed", path, exc.response.status_code, details
            ) from exc
        except httpx.TimeoutException as exc:
            raise PveApiError("Таймаут запроса POST", path) from exc
        except httpx.RequestError as exc:
            raise PveApiError("Ошибка транспорта POST", path) from exc
        except ValueError as exc:
            raise PveApiError("Некорректный JSON в ответе POST", path) from exc

        if not isinstance(body, dict) or "data" not in body:
            raise PveApiError("PVE API response is missing data", path)

        self._logger.info("pve_post", extra={"path": path, "outcome": "ok"})
        return body["data"]

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._auth.base_url}/api2/json{path}"

        try:
            client = self._client or self._make_client()
            response = await client.get(
                url,
                headers={
                    "Accept": "application/json",
                    "Authorization": self._auth.authorization_header,
                },
                params=params,
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
