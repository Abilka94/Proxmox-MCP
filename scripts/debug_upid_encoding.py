"""Test UPID URL encoding with actual PVE API calls."""

from __future__ import annotations

import asyncio
import urllib.parse

import httpx

from mcp_proxmox.config import load_config
from mcp_proxmox.pve.auth import auth_config_from_app_config


async def main() -> None:
    config = load_config("config/local.yaml")
    auth = auth_config_from_app_config(config)
    base = auth.base_url
    headers = {"Accept": "application/json", "Authorization": auth.authorization_header}

    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        # Get first UPID from task list
        resp = await client.get(f"{base}/api2/json/cluster/tasks", headers=headers)
        tasks = resp.json().get("data", [])
        if not tasks:
            print("No tasks found")
            return
        upid = tasks[0].get("upid", "")
        node = tasks[0].get("node", "")
        encoded = urllib.parse.quote(upid, safe="")
        print(f"UPID: {upid}")
        print(f"Node: {node}")
        print()

        # ── Cluster-level task_status ──
        print("=== Cluster-level task_status ===")
        path = f"/cluster/tasks/{encoded}/status"
        url = f"{base}/api2/json{path}"
        resp = await client.get(url, headers=headers)
        print(f"GET {path}: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  data: {resp.json().get('data')}")
        else:
            print(f"  {resp.text[:200]}")
        print()

        # ── Node-level task_status ──
        print("=== Node-level task_status ===")
        path = f"/nodes/{node}/tasks/{encoded}/status"
        url = f"{base}/api2/json{path}"
        resp = await client.get(url, headers=headers)
        print(f"GET {path}: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  data: {resp.json().get('data')}")
        else:
            print(f"  {resp.text[:200]}")
        print()

        # ── Task log (for comparison) ──
        print("=== Task log ===")
        path = f"/nodes/{node}/tasks/{encoded}/log"
        url = f"{base}/api2/json{path}"
        resp = await client.get(url, headers=headers)
        print(f"GET {path}: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            print(f"  lines: {len(data)}")
            for line in data[:3]:
                print(f"  {line.get('t','')[:80]}")
        else:
            print(f"  {resp.text[:200]}")

        # ── Try without trailing colon in UPID ──
        print()
        print("=== Node-level task_status (no trailing colon) ===")
        stripped = upid.rstrip(":")
        encoded2 = urllib.parse.quote(stripped, safe="")
        path = f"/nodes/{node}/tasks/{encoded2}/status"
        url = f"{base}/api2/json{path}"
        resp = await client.get(url, headers=headers)
        print(f"GET {path}: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  data: {resp.json().get('data')}")
        else:
            print(f"  {resp.text[:200]}")

        # ── Try with different UPID format (maybe needs ?upid= parameter) ──
        print()
        print("=== Node task_status via query param ===")
        path = f"/nodes/{node}/tasks/{encoded}/status"
        url = f"{base}/api2/json{path}"
        # httpx with params
        resp = await client.get(url, headers=headers, params={"upid": upid})
        print(f"GET {path}?upid=...: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  data: {resp.json().get('data')}")
        else:
            print(f"  {resp.text[:200]}")

        # ── Check node tasks list ──
        print()
        print("=== Node tasks list ===")
        resp = await client.get(f"{base}/api2/json/nodes/{node}/tasks", headers=headers, params={"limit": 3})
        print(f"GET /nodes/{node}/tasks?limit=3: {resp.status_code}")
        if resp.status_code == 200:
            tasks2 = resp.json().get("data", [])
            for t in tasks2:
                print(f"  upid={t.get('upid','')[:60]}")
            # Try task_status for each node-level task
            if tasks2:
                print()
                print("=== Node status for first node-level task ===")
                upid2 = urllib.parse.quote(tasks2[0].get("upid",""), safe="")
                path = f"/nodes/{node}/tasks/{upid2}/status"
                resp = await client.get(f"{base}/api2/json{path}", headers=headers)
                print(f"GET {path}: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  data: {resp.json().get('data')}")
                else:
                    print(f"  {resp.text[:200]}")

if __name__ == "__main__":
    asyncio.run(main())
