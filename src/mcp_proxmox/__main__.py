"""Command entrypoint for MCP-Proxmox."""

from __future__ import annotations

import asyncio
import sys

from mcp_proxmox.config import ConfigError, load_config
from mcp_proxmox.logging import configure_logging, get_logger
from mcp_proxmox.mcp.handlers import MinimalMcpServer
from mcp_proxmox.mcp.registry import create_default_registry
from mcp_proxmox.mcp.transport import StdioTransport
from mcp_proxmox.policy import PolicyEngine
from mcp_proxmox.pve.auth import auth_config_from_app_config
from mcp_proxmox.pve.client import PveClient


async def main() -> int:
    """Run the MCP stdio server."""

    try:
        config = load_config()
    except ConfigError as exc:
        print(f"config invalid: {exc}", file=sys.stderr)
        return 1

    configure_logging(config.logging, stream=sys.stderr)
    logger = get_logger("mcp_proxmox.main")
    logger.info("server_starting", extra={"connection_id": config.connection.id})

    policy = PolicyEngine(config.policy)
    pve_client = PveClient(auth_config_from_app_config(config))
    registry = create_default_registry(config, pve_client)
    server = MinimalMcpServer(registry, policy)
    transport = StdioTransport(server)
    return await transport.serve_forever()


def cli() -> int:
    """Sync entry point for the installed console script."""
    return asyncio.run(main())


if __name__ == "__main__":
    raise SystemExit(cli())
