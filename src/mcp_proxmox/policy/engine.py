"""Policy engine for MCP-Proxmox tools."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from mcp_proxmox.config.models import PolicyConfig, PolicyMode


class ToolTier(StrEnum):
    """Tool permission tiers."""

    READ = "READ"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


class PolicyDenied(PermissionError):
    """Raised when policy denies a tool call."""


@dataclass(frozen=True)
class ToolPolicy:
    """Policy metadata attached to a tool."""

    name: str
    tier: ToolTier


class PolicyEngine:
    """Evaluate tool calls against the configured policy mode."""

    def __init__(self, config: PolicyConfig) -> None:
        self._config = config

    @property
    def mode(self) -> PolicyMode:
        return self._config.mode

    def authorize(self, policy: ToolPolicy) -> None:
        """Authorize a tool call or raise :class:`PolicyDenied`."""

        if self._config.mode == PolicyMode.READ_ONLY and policy.tier != ToolTier.READ:
            raise PolicyDenied(
                f"Tool {policy.name!r} requires tier {policy.tier.value}, "
                f"but policy mode is {self._config.mode.value}"
            )
