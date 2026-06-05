"""Authentication and connection settings for the Proxmox VE API."""

from __future__ import annotations

from dataclasses import dataclass

from mcp_proxmox.config.models import AppConfig


@dataclass(frozen=True)
class PveAuthConfig:
    """Resolved PVE API connection settings."""

    base_url: str
    token_id: str
    token_secret: str
    verify_ssl: bool
    timeout_sec: float

    @property
    def authorization_header(self) -> str:
        return f"PVEAPIToken={self.token_id}={self.token_secret}"


def auth_config_from_app_config(config: AppConfig) -> PveAuthConfig:
    """Build a PVE auth config from the application config."""

    return PveAuthConfig(
        base_url=str(config.connection.host).rstrip("/"),
        token_id=config.connection.token_id,
        token_secret=config.connection.token_secret,
        verify_ssl=config.connection.verify_ssl,
        timeout_sec=float(config.orchestrator.node_request_timeout_sec),
    )
