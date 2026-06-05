"""Load and validate MCP-Proxmox configuration."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from mcp_proxmox.config.models import AppConfig

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


class ConfigError(RuntimeError):
    """Raised when configuration cannot be loaded or validated."""


def load_config(path: str | Path | None = None) -> AppConfig:
    """Load config from YAML and validate it as :class:`AppConfig`."""

    config_path = Path(path or os.environ.get("MCP_PROXMOX_CONFIG", "config/default.yaml"))
    raw = _load_yaml_file(config_path)
    expanded = expand_env(raw)
    return parse_config(expanded)


def parse_config(data: Mapping[str, Any]) -> AppConfig:
    """Validate already-loaded config data."""

    try:
        return AppConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc


def expand_env(value: Any) -> Any:
    """Expand ${VAR} placeholders and fail if a referenced variable is missing."""

    if isinstance(value, str):
        return ENV_PATTERN.sub(_replace_env, value)
    if isinstance(value, list):
        return [expand_env(item) for item in value]
    if isinstance(value, dict):
        return {key: expand_env(item) for key, item in value.items()}
    return value


def _replace_env(match: re.Match[str]) -> str:
    name = match.group(1)
    try:
        return os.environ[name]
    except KeyError as exc:
        raise ConfigError(f"Missing required environment variable: {name}") from exc


def _load_yaml_file(path: Path) -> Mapping[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        text = file.read()

    try:
        import yaml
    except ModuleNotFoundError:
        data = _parse_simple_yaml(text)
    else:
        data = yaml.safe_load(text)

    if not isinstance(data, dict):
        raise ConfigError(f"Config root must be a mapping: {path}")

    return data


def _parse_simple_yaml(text: str) -> Mapping[str, Any]:
    """Parse the simple mapping-only YAML subset used by config/default.yaml."""

    root: dict[str, Any] = {}
    stack: list[tuple[int, MutableMapping[str, Any]]] = [(-1, root)]

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise ConfigError(f"Invalid YAML indentation at line {line_number}")

        stripped = line.strip()
        if ":" not in stripped:
            raise ConfigError(f"Invalid YAML mapping at line {line_number}")

        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise ConfigError(f"Missing YAML key at line {line_number}")

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ConfigError(f"Invalid YAML nesting at line {line_number}")

        parent = stack[-1][1]
        if raw_value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(raw_value)

    return root


def _parse_scalar(value: str) -> str | int | bool:
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value
