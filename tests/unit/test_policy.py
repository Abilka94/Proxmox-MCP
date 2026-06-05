from __future__ import annotations

import unittest

from mcp_proxmox.config.models import PolicyConfig, PolicyMode
from mcp_proxmox.policy import PolicyDenied, PolicyEngine, ToolPolicy, ToolTier


class PolicyEngineTests(unittest.TestCase):
    def test_read_only_allows_read_tools(self) -> None:
        engine = PolicyEngine(PolicyConfig(mode=PolicyMode.READ_ONLY))

        engine.authorize(ToolPolicy(name="pve_nodes_list", tier=ToolTier.READ))

    def test_read_only_denies_operator_tools(self) -> None:
        engine = PolicyEngine(PolicyConfig(mode=PolicyMode.READ_ONLY))

        with self.assertRaises(PolicyDenied):
            engine.authorize(ToolPolicy(name="pve_node_reboot", tier=ToolTier.OPERATOR))

    def test_read_only_denies_admin_tools(self) -> None:
        engine = PolicyEngine(PolicyConfig(mode=PolicyMode.READ_ONLY))

        with self.assertRaises(PolicyDenied):
            engine.authorize(ToolPolicy(name="pve_cluster_delete", tier=ToolTier.ADMIN))


if __name__ == "__main__":
    unittest.main()
