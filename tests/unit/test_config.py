from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mcp_proxmox.config import ConfigError, expand_env, load_config, parse_config


def valid_config() -> dict[str, object]:
    return {
        "connection": {
            "id": "local",
            "host": "https://pve.example.local:8006",
            "token_id": "root@pam!mcp-proxmox",
            "token_secret": "secret",
            "verify_ssl": True,
        },
        "policy": {
            "mode": "READ_ONLY",
            "memory": {"allow_write": True},
        },
        "orchestrator": {
            "max_concurrent_per_node": 5,
            "max_concurrent_cluster": 15,
            "node_request_timeout_sec": 30,
            "aggregate_threshold": 500,
        },
        "cache": {
            "cluster_resources_ttl_sec": 30,
            "node_status_ttl_sec": 15,
        },
        "logging": {
            "level": "INFO",
            "format": "console",
        },
        "audit": {
            "path": "data/audit.log",
        },
        "subsystems": {
            "logs": {
                "enabled": True,
                "max_lines": 500,
            },
        },
    }


class ConfigTests(unittest.TestCase):
    def test_parse_config_accepts_valid_config(self) -> None:
        config = parse_config(valid_config())

        self.assertEqual(config.connection.id, "local")
        self.assertEqual(str(config.connection.host), "https://pve.example.local:8006/")
        self.assertEqual(config.policy.mode.value, "READ_ONLY")

    def test_parse_config_rejects_invalid_policy_mode(self) -> None:
        data = valid_config()
        policy = data["policy"]
        assert isinstance(policy, dict)
        policy["mode"] = "ADMIN"

        with self.assertRaises(ConfigError):
            parse_config(data)

    def test_parse_config_rejects_extra_keys(self) -> None:
        data = valid_config()
        data["unexpected"] = True

        with self.assertRaises(ConfigError):
            parse_config(data)

    def test_expand_env_replaces_required_placeholders(self) -> None:
        with patch.dict(os.environ, {"PVE_TOKEN_SECRET": "from-env"}):
            expanded = expand_env({"token_secret": "${PVE_TOKEN_SECRET}"})

        self.assertEqual(expanded["token_secret"], "from-env")

    def test_expand_env_rejects_missing_placeholder(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ConfigError):
                expand_env({"token_secret": "${PVE_TOKEN_SECRET}"})

    def test_load_config_reads_yaml_and_expands_env(self) -> None:
        yaml_text = """
connection:
  id: "local"
  host: "${PVE_HOST}"
  token_id: "${PVE_TOKEN_ID}"
  token_secret: "${PVE_TOKEN_SECRET}"
  verify_ssl: true
policy:
  mode: READ_ONLY
  memory:
    allow_write: true
orchestrator:
  max_concurrent_per_node: 5
  max_concurrent_cluster: 15
  node_request_timeout_sec: 30
  aggregate_threshold: 500
cache:
  cluster_resources_ttl_sec: 30
  node_status_ttl_sec: 15
logging:
  level: INFO
  format: console
audit:
  path: "data/audit.log"
subsystems:
  logs:
    enabled: true
    max_lines: 500
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config.yaml"
            path.write_text(yaml_text, encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "PVE_HOST": "https://pve.example.local:8006",
                    "PVE_TOKEN_ID": "root@pam!mcp-proxmox",
                    "PVE_TOKEN_SECRET": "secret",
                },
                clear=True,
            ):
                config = load_config(path)

        self.assertEqual(config.connection.token_secret, "secret")


if __name__ == "__main__":
    unittest.main()
