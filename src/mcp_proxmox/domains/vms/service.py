"""VM domain read helpers."""

from __future__ import annotations

from mcp_proxmox.pve.client import PveClient


async def vm_list(client: PveClient) -> dict[str, object]:
    """Return all QEMU VMs in the cluster."""

    vms = await client.get_vms()
    return {
        "count": len(vms),
        "vms": [vm.model_dump(mode="json") for vm in vms],
    }


async def vm_status(client: PveClient, node: str, vmid: int) -> dict[str, object]:
    """Return detailed status for a specific VM."""

    status = await client.get_vm_status(node, vmid)
    return status.model_dump(mode="json")


async def vm_config(client: PveClient, node: str, vmid: int) -> dict[str, object]:
    """Return full configuration for a specific VM."""

    config = await client.get_vm_config(node, vmid)
    return config.model_dump(mode="json")
