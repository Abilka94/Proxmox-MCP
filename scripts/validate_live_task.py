"""Live validation for Phase 1B.1 Task Domain tools."""

from __future__ import annotations

import argparse
import asyncio
import sys

from mcp_proxmox.config import ConfigError, load_config
from mcp_proxmox.domains.tasks import task_list, task_log, task_status
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
        line += f"  \u2014 {detail}"
    print(line)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1B.1 Task Domain live validation")
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

    try:
        auth = auth_config_from_app_config(config)
    except Exception as exc:
        print(f"AuthError: {exc}", file=sys.stderr)
        return 1

    client = PveClient(auth)

    # ── Discovery ─────────────────────────────────────────────────

    try:
        nodes = await client.get_nodes()
    except PveApiError as exc:
        print(f"Cannot get nodes \u2014 aborting: {exc.message}", file=sys.stderr)
        return 1

    node_names = [n.node for n in nodes]
    print(f"discovered {len(node_names)} node(s): {', '.join(node_names)}")
    print()

    # ── T1: task_list without filters ──────────────────────────────

    print("--- task_list (no filters) ---")
    try:
        result = await task_list(client)
        count = result.get("count", 0)
        tasks = result.get("tasks", [])
        record("task_list (no filters)", PASS, f"{count} task(s)")
        for t in tasks[:3]:
            upid = t.get("upid", "?")
            status = t.get("status", "?")
            rec_node = t.get("node", "?")
            print(f"         {upid[:60]}  status={status}  node={rec_node}")
        if count > 3:
            print(f"         ... and {count - 3} more")
    except Exception as exc:
        record("task_list (no filters)", FAIL, f"{type(exc).__name__}: {exc}")
        tasks = []
    print()

    # ── T2: task_list with limit ───────────────────────────────────

    print("--- task_list (limit=3) ---")
    try:
        result = await task_list(client, limit=3)
        count = result.get("count", 0)
        if count <= 3:
            record("task_list (limit=3)", PASS, f"{count} task(s)")
        else:
            record("task_list (limit=3)", FAIL, f"expected <= 3, got {count}")
    except Exception as exc:
        record("task_list (limit=3)", FAIL, f"{type(exc).__name__}: {exc}")
    print()

    # ── T3: task_list status=running ───────────────────────────────

    print("--- task_list (status=running) ---")
    try:
        result = await task_list(client, status="running", limit=50)
        count = result.get("count", 0)
        all_running = all(t.get("status") == "running" for t in result.get("tasks", []))
        if all_running:
            record("task_list (status=running)", PASS, f"{count} running task(s)")
        else:
            record("task_list (status=running)", FAIL, "not all returned tasks have status=running")
    except Exception as exc:
        record("task_list (status=running)", FAIL, f"{type(exc).__name__}: {exc}")
    print()

    # ── T4: task_list status=stopped ───────────────────────────────

    print("--- task_list (status=stopped) ---")
    try:
        result = await task_list(client, status="stopped", limit=50)
        count = result.get("count", 0)
        all_stopped = all(t.get("status") == "stopped" for t in result.get("tasks", []))
        if all_stopped:
            record("task_list (status=stopped)", PASS, f"{count} stopped task(s)")
        else:
            record("task_list (status=stopped)", FAIL, "not all returned tasks have status=stopped")
    except Exception as exc:
        record("task_list (status=stopped)", FAIL, f"{type(exc).__name__}: {exc}")
    print()

    # ── T5: task_list with node filter ────────────────────────────

    print("--- task_list (node filter) ---")
    for n in node_names:
        tool_name = f"task_list (node={n})"
        try:
            result = await task_list(client, node=n, limit=10)
            count = result.get("count", 0)
            all_from_node = all(t.get("node") == n for t in result.get("tasks", []))
            if all_from_node:
                record(tool_name, PASS, f"{count} task(s)")
            else:
                record(tool_name, FAIL, "not all tasks belong to the filtered node")
        except Exception as exc:
            record(tool_name, FAIL, f"{type(exc).__name__}: {exc}")
    print()

    # ── Pick UPIDs for further tests ───────────────────────────────

    all_upids: list[tuple[str, str]] = []
    stopped_upids: list[tuple[str, str]] = []
    running_upids: list[tuple[str, str]] = []

    try:
        all_result = await task_list(client, limit=50)
        for t in all_result.get("tasks", []):
            upid = t.get("upid", "")
            node = t.get("node", "")
            status = t.get("status", "")
            if upid and node:
                all_upids.append((upid, node))
                if status == "running":
                    running_upids.append((upid, node))
    except Exception:
        pass

    # ── S1: task_status for any existing task ──────────────────────

    print("--- task_status (existing UPID) ---")
    if all_upids:
        upid, node = all_upids[0]
        try:
            result = await task_status(client, upid, node=node)
            status = result.get("status", "?")
            exitstatus = result.get("exitstatus")
            upid_returned = result.get("upid", "")
            record("task_status (existing)", PASS, f"status={status} exitstatus={exitstatus}")
            if upid_returned != upid:
                record("task_status (existing)", FAIL, f"UPID mismatch: returned {upid_returned}")
        except Exception as exc:
            record("task_status (existing)", FAIL, f"{type(exc).__name__}: {exc}")
    else:
        record("task_status (existing)", SKIP, "no tasks found")
    print()

    # ── S2: task_status cluster→node fallback ──────────────────────

    print("--- task_status (cluster fallback) ---")
    if len(all_upids) >= 1:
        upid, upid_node = all_upids[0]
        try:
            result = await task_status(client, upid, node=upid_node)
            record("task_status (with node param)", PASS, f"status={result.get('status','?')}")
        except Exception as exc:
            record("task_status (with node param)", FAIL, f"{type(exc).__name__}: {exc}")
    else:
        record("task_status (with node param)", SKIP, "no tasks found")
    print()

    # ── S3: task_status non-existent UPID ──────────────────────────

    print("--- task_status (non-existent UPID) ---")
    try:
        fake_upid = "UPID:pve:00000000:00000000:00000000:test:root@pam:"
        result = await task_status(client, fake_upid)
        record("task_status (invalid UPID)", FAIL, "expected error, got result")
    except PveApiError as exc:
        record("task_status (invalid UPID)", PASS, f"PveApiError ({exc.status_code})")
    except Exception as exc:
        record("task_status (invalid UPID)", FAIL, f"{type(exc).__name__}: {exc}")
    print()

    # ── L1: task_log for existing task ─────────────────────────────

    print("--- task_log (existing UPID) ---")
    if all_upids:
        upid, node = all_upids[0]
        try:
            result = await task_log(client, upid, node)
            total = result.get("total_lines", 0)
            lines = result.get("lines", [])
            record("task_log (existing)", PASS, f"{total} line(s)")
            for line in lines[:5]:
                text = line.get("text", "")[:80]
                print(f"         {text}")
            if total > 5:
                print(f"         ... and {total - 5} more")
            # Verify text mapping
            if total > 0:
                first_line = lines[0]
                if "text" in first_line:
                    record("task_log (text mapping)", PASS, f"text field present")
                else:
                    record("task_log (text mapping)", FAIL, "text field missing")
        except Exception as exc:
            record("task_log (existing)", FAIL, f"{type(exc).__name__}: {exc}")
    else:
        record("task_log (existing)", SKIP, "no tasks found")
    print()

    # ── L2: task_log with start offset ─────────────────────────────

    print("--- task_log (start=0) ---")
    if all_upids:
        upid, node = all_upids[0]
        try:
            result_full = await task_log(client, upid, node)
            result_offset = await task_log(client, upid, node, start=0)
            if result_full["total_lines"] == result_offset.get("total_lines", 0):
                record("task_log (start=0)", PASS, f"{result_offset['total_lines']} line(s)")
            else:
                record("task_log (start=0)", FAIL, "start=0 should return all lines")
        except Exception as exc:
            record("task_log (start=0)", FAIL, f"{type(exc).__name__}: {exc}")
    else:
        record("task_log (start=0)", SKIP, "no tasks found")
    print()

    # ── L3: task_log non-existent UPID ─────────────────────────────

    print("--- task_log (non-existent UPID) ---")
    try:
        fake_upid = "UPID:pve:00000000:00000000:00000000:test:root@pam:"
        result = await task_log(client, fake_upid, node_names[0])
        record("task_log (invalid UPID)", FAIL, "expected error, got result")
    except PveApiError:
        record("task_log (invalid UPID)", PASS, "PveApiError raised")
    except Exception as exc:
        record("task_log (invalid UPID)", FAIL, f"{type(exc).__name__}: {exc}")
    print()

    # ── E1: Empty result — non-existent node —──────────────────────

    print("--- edge: empty result (bad node) ---")
    try:
        result = await task_list(client, node="nonexistent_node_xyz", limit=1)
        count = result.get("count", 0)
        if count == 0:
            record("empty result (bad node)", PASS, "count=0, tasks=[]")
        else:
            record("empty result (bad node)", FAIL, f"expected 0, got {count}")
    except PveApiError as exc:
        record("empty result (bad node)", PASS, f"PveApiError ({exc.status_code}) — expected for bad node")
    except Exception as exc:
        record("empty result (bad node)", FAIL, f"{type(exc).__name__}: {exc}")
    print()

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
