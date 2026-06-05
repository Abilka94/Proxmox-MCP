"""Validate MCP-Proxmox configuration."""

from __future__ import annotations

import argparse
import sys

from mcp_proxmox.config import ConfigError, load_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MCP-Proxmox configuration")
    parser.add_argument(
        "--config",
        default=None,
        help="Path to YAML config. Defaults to MCP_PROXMOX_CONFIG or config/default.yaml.",
    )
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"config invalid: {exc}", file=sys.stderr)
        return 1

    print(f"config valid: connection={config.connection.id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
