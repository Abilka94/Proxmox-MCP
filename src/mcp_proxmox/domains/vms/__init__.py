"""QEMU VM domain service."""

from mcp_proxmox.domains.vms.service import vm_list, vm_status

__all__ = ["vm_list", "vm_status"]
