from __future__ import annotations

import io
import json
import unittest

from mcp_proxmox.logging import configure_logging, correlation_context, get_logger, redact


class LoggingTests(unittest.TestCase):
    def test_json_log_contains_correlation_id(self) -> None:
        stream = io.StringIO()
        configure_logging(level="INFO", log_format="json", stream=stream)
        logger = get_logger("mcp_proxmox.test")

        with correlation_context("corr-1"):
            logger.info("tool_call", extra={"tool": "pve_nodes_list"})

        event = json.loads(stream.getvalue())
        self.assertEqual(event["correlation_id"], "corr-1")
        self.assertEqual(event["event"], "tool_call")
        self.assertEqual(event["tool"], "pve_nodes_list")

    def test_json_log_redacts_tokens(self) -> None:
        stream = io.StringIO()
        configure_logging(level="INFO", log_format="json", stream=stream)
        logger = get_logger("mcp_proxmox.test")

        logger.info("auth", extra={"token_secret": "super-secret"})

        event = json.loads(stream.getvalue())
        self.assertEqual(event["token_secret"], "[REDACTED]")

    def test_redact_nested_mapping(self) -> None:
        value = redact({"connection": {"authorization": "Bearer token", "id": "local"}})

        self.assertEqual(value["connection"]["authorization"], "[REDACTED]")
        self.assertEqual(value["connection"]["id"], "local")


if __name__ == "__main__":
    unittest.main()
