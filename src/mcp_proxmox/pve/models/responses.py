"""Response models for Proxmox VE read APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class PveResponseModel(BaseModel):
    """Base response model that ignores unknown fields from PVE."""

    model_config = ConfigDict(extra="ignore")


class ClusterStatusEntry(PveResponseModel):
    type: str
    id: str | None = None
    name: str | None = None
    ip: str | None = None
    level: str | None = None
    local: int | None = None
    nodeid: int | None = None
    online: int | None = None
    quorate: int | None = None
    version: int | None = None


class NodeInfo(PveResponseModel):
    node: str
    status: str | None = None
    cpu: float | None = None
    maxcpu: int | None = None
    mem: int | None = None
    maxmem: int | None = None
    disk: int | None = None
    maxdisk: int | None = None
    level: str | None = None
    uptime: int | None = None
    type: str | None = None
    id: str | None = None
    ssl_fingerprint: str | None = None


class NodeStatus(PveResponseModel):
    cpu: float | None = None
    loadavg: list[float] | None = None
    memory: dict[str, Any] | None = None
    rootfs: dict[str, Any] | None = None
    swap: dict[str, Any] | None = None
    uptime: int | None = None
    kversion: str | None = None
    pveversion: str | None = None
    cpuinfo: dict[str, Any] | None = None


class VmResource(PveResponseModel):
    id: str
    node: str
    type: str
    vmid: int
    name: str | None = None
    status: str | None = None
    cpu: float | None = None
    mem: int | None = None
    maxmem: int | None = None
    disk: int | None = None
    maxdisk: int | None = None
    uptime: int | None = None


class VmStatus(PveResponseModel):
    status: str | None = None
    cpu: float | None = None
    mem: int | None = None
    maxmem: int | None = None
    disk: int | None = None
    maxdisk: int | None = None
    uptime: int | None = None
    name: str | None = None
    qmpstatus: str | None = None
    pid: int | None = None
    cpus: int | None = None
    tags: str | None = None
    template: int | None = None


class LxcResource(PveResponseModel):
    id: str
    node: str
    type: str
    vmid: int
    name: str | None = None
    status: str | None = None
    cpu: float | None = None
    mem: int | None = None
    maxmem: int | None = None
    swap: int | None = None
    maxswap: int | None = None
    disk: int | None = None
    maxdisk: int | None = None
    uptime: int | None = None


class LxcStatus(PveResponseModel):
    status: str | None = None
    cpu: float | None = None
    mem: int | None = None
    maxmem: int | None = None
    swap: int | None = None
    maxswap: int | None = None
    disk: int | None = None
    maxdisk: int | None = None
    uptime: int | None = None
    name: str | None = None
    cpus: int | None = None
    tags: str | None = None
    template: int | None = None


class StorageResource(PveResponseModel):
    id: str
    node: str
    type: str
    storage: str
    status: str | None = None
    used: int | None = None
    avail: int | None = None
    total: int | None = None
    used_fraction: float | None = None
    content: str | None = None


class StorageStatus(PveResponseModel):
    total: int | None = None
    used: int | None = None
    avail: int | None = None
    used_fraction: float | None = None
    active: int | None = None
    content: str | None = None
    enabled: int | None = None
    shared: int | None = None


class NetworkInterface(PveResponseModel):
    iface: str
    method: str | None = None
    type: str | None = None
    active: int | None = None
    cidr: str | None = None
    cidr6: str | None = None
    bridge_ports: str | None = None
    bridge_fd: str | None = None
    bridge_stp: str | None = None
    priority: int | None = None
    comments: str | None = None
    autostart: int | None = None
    families: str | None = None


class NodeUpdateEntry(PveResponseModel):
    title: str
    package: str | None = None
    version: str | None = None
    old_version: str | None = None
    arch: str | None = None
    description: str | None = None
    priority: str | None = None
