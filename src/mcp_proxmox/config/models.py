"""Configuration models for MCP-Proxmox."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PositiveInt


class StrictModel(BaseModel):
    """Base model that rejects unknown configuration keys."""

    model_config = ConfigDict(extra="forbid")


class PolicyMode(StrEnum):
    """Supported policy modes for Phase 1A."""

    READ_ONLY = "READ_ONLY"


class LogFormat(StrEnum):
    """Supported application log formats."""

    JSON = "json"
    CONSOLE = "console"


class LogLevel(StrEnum):
    """Supported application log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ConnectionConfig(StrictModel):
    id: str = Field(min_length=1)
    host: HttpUrl
    token_id: str = Field(min_length=1)
    token_secret: str = Field(min_length=1)
    verify_ssl: bool = True


class MemoryPolicyConfig(StrictModel):
    allow_write: bool = True


class PolicyConfig(StrictModel):
    mode: PolicyMode = PolicyMode.READ_ONLY
    memory: MemoryPolicyConfig = Field(default_factory=MemoryPolicyConfig)


class OrchestratorConfig(StrictModel):
    max_concurrent_per_node: PositiveInt = 5
    max_concurrent_cluster: PositiveInt = 15
    node_request_timeout_sec: PositiveInt = 30
    aggregate_threshold: PositiveInt = 500


class CacheConfig(StrictModel):
    cluster_resources_ttl_sec: int = Field(default=30, ge=0)
    node_status_ttl_sec: int = Field(default=15, ge=0)


class LoggingConfig(StrictModel):
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.CONSOLE


class AuditConfig(StrictModel):
    path: str = Field(default="data/audit.log", min_length=1)


class LogsSubsystemConfig(StrictModel):
    enabled: bool = True
    max_lines: PositiveInt = 500


class SubsystemsConfig(StrictModel):
    logs: LogsSubsystemConfig = Field(default_factory=LogsSubsystemConfig)


class AppConfig(StrictModel):
    connection: ConnectionConfig
    policy: PolicyConfig
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    subsystems: SubsystemsConfig = Field(default_factory=SubsystemsConfig)
