"""Debug which params /cluster/tasks vs /nodes/{node}/tasks accepts."""

from __future__ import annotations

import asyncio
import httpx

from mcp_proxmox.config import load_config
from mcp_proxmox.pve.auth import auth_config_from_app_config


async def main() -> None:
    config = load_config("config/local.yaml")
    auth = auth_config_from_app_config(config)
    base = auth.base_url
    headers = {"Accept": "application/json", "Authorization": auth.authorization_header}

    # Use httpx directly with a single client and longer timeout
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        # Test cluster-level endpoint without params
        resp = await client.get(f"{base}/api2/json/cluster/tasks", headers=headers)
        print(f"cluster/tasks (no params): {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json().get("data", [])
            print(f"  tasks: {len(data)}")
            if data:
                print(f"  first status: {data[0].get('status')}")
                print(f"  first has 'status' key: {'status' in data[0]}")

        # Test cluster-level with status param
        resp = await client.get(f"{base}/api2/json/cluster/tasks", headers=headers, params={"status": "running"})
        print(f"\ncluster/tasks?status=running: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  {resp.text[:300]}")

        # Test node-level tasks
        for node in ["pve", "pve2", "pve3"]:
            resp = await client.get(f"{base}/api2/json/nodes/{node}/tasks", headers=headers)
            print(f"\nnodes/{node}/tasks (no params): {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                print(f"  tasks: {len(data)}")
            else:
                print(f"  {resp.text[:200]}")

            # Test node-level with status param
            resp = await client.get(f"{base}/api2/json/nodes/{node}/tasks", headers=headers, params={"status": "running"})
            print(f"nodes/{node}/tasks?status=running: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                print(f"  tasks: {len(data)}")
            else:
                print(f"  {resp.text[:200]}")

            # Test node-level with limit
            resp = await client.get(f"{base}/api2/json/nodes/{node}/tasks", headers=headers, params={"limit": 5})
            print(f"nodes/{node}/tasks?limit=5: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                print(f"  tasks: {len(data)}")
            else:
                print(f"  {resp.text[:200]}")


if __name__ == "__main__":
    asyncio.run(main())
