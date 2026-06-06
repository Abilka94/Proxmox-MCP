"""Live PVE cluster connection test — Validation Sprint only."""

from __future__ import annotations

import argparse
import asyncio
import sys

from mcp_proxmox.config import ConfigError, load_config
from mcp_proxmox.pve.auth import auth_config_from_app_config
from mcp_proxmox.pve.client import PveApiError, PveClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Test live PVE cluster connection")
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

    try:
        nodes = asyncio.run(client.get_nodes())
    except PveApiError as exc:
        print(f"PveApiError ({exc.status_code}): {exc.message}", file=sys.stderr)
        if exc.details:
            print(f"  details: {exc.details[:200]}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ConnectionError: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print(f"connected: {len(nodes)} node(s)")
    for n in nodes:
        print(f"  - {n.node} ({n.status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
