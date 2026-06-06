"""Live MCP tool validation — calls each tool against the real cluster."""

from __future__ import annotations

import argparse
import asyncio
import sys
import traceback

from mcp_proxmox.config import ConfigError, load_config
from mcp_proxmox.domains.cluster import cluster_info
from mcp_proxmox.domains.containers import container_config, container_list
from mcp_proxmox.domains.network import network_list
from mcp_proxmox.domains.nodes import list_nodes, node_status
from mcp_proxmox.domains.storage import storage_content, storage_list
from mcp_proxmox.domains.updates import cluster_updates, node_updates
from mcp_proxmox.domains.vms import vm_config, vm_list
from mcp_proxmox.mcp.registry import ALL_TOOLS
from mcp_proxmox.pve.auth import auth_config_from_app_config
from mcp_proxmox.pve.client import PveApiError, PveClient

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results: list[dict[str, object]] = []


def record(name: str, status: str, detail: str = "") -> None:
    results.append({"tool": name, "status": status, "detail": detail})
    marker = "[OK]" if status == PASS else "[FAIL]" if status == FAIL else "[SKIP]"
    line = f"  {marker} {name}"
    if detail:
        line += f"  — {detail}"
    print(line)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Live MCP tool validation")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to YAML config. Defaults to MCP_PROXMOX_CONFIG or config/default.yaml.",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"ConfigError: {exc}", file=sys.stderr)
        return 1

    print(f"config loaded: connection={config.connection.id}")
    print(f"tools to validate: {len(ALL_TOOLS)} ({', '.join(ALL_TOOLS)})")
    print()

    try:
        auth = auth_config_from_app_config(config)
    except Exception as exc:
        print(f"AuthError: {exc}", file=sys.stderr)
        return 1

    client = PveClient(auth)

    # ── Phase 1: Tool-less helpers (discovery) ──────────────────────

    try:
        nodes = await client.get_nodes()
    except PveApiError as exc:
        print(f"Cannot get nodes — aborting: {exc.message}", file=sys.stderr)
        return 1

    node_names = [n.node for n in nodes]
    print(f"discovered {len(node_names)} node(s): {', '.join(node_names)}")
    print()

    # ── Phase 2: Tools without required params ──────────────────────

    # 1. server_info (static — no PVE call)
    record("server_info", PASS, "static info (no PVE call)")

    # 2. list_nodes
    try:
        result = await list_nodes(client)
        count = len(result.get("nodes", []))
        record("list_nodes", PASS, f"{count} node(s)")
    except Exception as exc:
        record("list_nodes", FAIL, f"{type(exc).__name__}: {exc}")

    # 3. cluster_info
    try:
        result = await cluster_info(client)
        cname = result.get("name", "?")
        ncount = result.get("nodes", {}).get("total", 0)
        record("cluster_info", PASS, f"cluster={cname}, {ncount} node(s)")
    except Exception as exc:
        record("cluster_info", FAIL, f"{type(exc).__name__}: {exc}")

    # ── Phase 3: node_status for each node ─────────────────────────

    for n in node_names:
        tool_name = f"node_status({n})"
        try:
            result = await node_status(client, n)
            if "error" in result:
                record(tool_name, FAIL, str(result["error"]))
            else:
                record(tool_name, PASS, f"cpu={result.get('cpu','?')}, mem={result.get('memory','?')}")
        except Exception as exc:
            record(tool_name, FAIL, f"{type(exc).__name__}: {exc}")

    # ── Phase 4: vm_list + vm_config for first VM ──────────────────

    try:
        vms = await vm_list(client)
        vm_count = len(vms.get("vms", []))
        record("vm_list", PASS, f"{vm_count} VM(s)")
        if vm_count > 0:
            first_vm = vms["vms"][0]
            vm_node = first_vm.get("node", node_names[0])
            vm_vmid = first_vm.get("vmid", 0)
            try:
                result = await vm_config(client, vm_node, vm_vmid)
                record("vm_config", PASS, f"VM {vm_vmid} on {vm_node}")
            except Exception as exc:
                record("vm_config", FAIL, f"{type(exc).__name__}: {exc}")
        else:
            record("vm_config", SKIP, "no VMs found")
    except Exception as exc:
        record("vm_list", FAIL, f"{type(exc).__name__}: {exc}")
        record("vm_config", SKIP, "vm_list failed")

    # ── Phase 5: container_list + container_config ─────────────────

    try:
        ctns = await container_list(client)
        ctn_count = len(ctns.get("containers", []))
        record("container_list", PASS, f"{ctn_count} container(s)")
        if ctn_count > 0:
            first_ctn = ctns["containers"][0]
            ctn_node = first_ctn.get("node", node_names[0])
            ctn_vmid = first_ctn.get("vmid", 0)
            try:
                result = await container_config(client, ctn_node, ctn_vmid)
                record("container_config", PASS, f"CT {ctn_vmid} on {ctn_node}")
            except Exception as exc:
                record("container_config", FAIL, f"{type(exc).__name__}: {exc}")
        else:
            record("container_config", SKIP, "no containers found")
    except Exception as exc:
        record("container_list", FAIL, f"{type(exc).__name__}: {exc}")
        record("container_config", SKIP, "container_list failed")

    # ── Phase 6: storage_list + storage_content ────────────────────

    try:
        storages = await storage_list(client)
        st_count = len(storages.get("storages", []))
        record("storage_list", PASS, f"{st_count} storage(s)")
        if st_count > 0:
            first_st = storages["storages"][0]
            st_node = first_st.get("node", node_names[0])
            st_id = first_st.get("storage", "")
            try:
                result = await storage_content(client, st_node, st_id)
                item_count = len(result.get("items", []))
                record("storage_content", PASS, f"{item_count} item(s) on {st_id}")
            except Exception as exc:
                record("storage_content", FAIL, f"{type(exc).__name__}: {exc}")
        else:
            record("storage_content", SKIP, "no storages found")
    except Exception as exc:
        record("storage_list", FAIL, f"{type(exc).__name__}: {exc}")
        record("storage_content", SKIP, "storage_list failed")

    # ── Phase 7: network_list ──────────────────────────────────────

    for n in node_names:
        tool_name = f"network_list({n})"
        try:
            result = await network_list(client, n)
            if_count = len(result.get("interfaces", []))
            record(tool_name, PASS, f"{if_count} interface(s)")
        except Exception as exc:
            record(tool_name, FAIL, f"{type(exc).__name__}: {exc}")

    # ── Phase 8: node_updates ──────────────────────────────────────

    for n in node_names:
        tool_name = f"node_updates({n})"
        try:
            result = await node_updates(client, n)
            up_count = len(result.get("updates", []))
            record(tool_name, PASS, f"{up_count} pending update(s)")
        except Exception as exc:
            record(tool_name, FAIL, f"{type(exc).__name__}: {exc}")

    # ── Phase 9: cluster_updates ───────────────────────────────────

    try:
        result = await cluster_updates(client)
        total = result.get("total_count", 0)
        record("cluster_updates", PASS, f"{total} pending update(s) across cluster")
    except Exception as exc:
        record("cluster_updates", FAIL, f"{type(exc).__name__}: {exc}")

    # ── Summary ────────────────────────────────────────────────────

    passed = sum(1 for r in results if r["status"] == PASS)
    failed = sum(1 for r in results if r["status"] == FAIL)
    skipped = sum(1 for r in results if r["status"] == SKIP)

    print()
    print(f"results: {passed} passed, {failed} failed, {skipped} skipped / {len(results)} total")

    if failed > 0:
        print()
        print("failures:")
        for r in results:
            if r["status"] == FAIL:
                print(f"  {r['tool']}: {r['detail']}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
