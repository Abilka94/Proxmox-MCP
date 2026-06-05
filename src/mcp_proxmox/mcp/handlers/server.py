"""Minimal MCP JSON-RPC request handling. Async, spec-compliant."""

from __future__ import annotations

import json
from typing import Any

from mcp_proxmox.logging import correlation_context, get_logger
from mcp_proxmox.mcp.registry.tools import ToolRegistry
from mcp_proxmox.policy import PolicyDenied, PolicyEngine

JSON_RPC_VERSION = "2.0"
DEFAULT_PROTOCOL_VERSION = "2024-11-05"


class McpProtocolError(RuntimeError):
    """Raised for malformed MCP protocol usage."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class MinimalMcpServer:
    """Serve a tiny subset of MCP over JSON-RPC for Phase 1A bootstrap."""

    def __init__(self, registry: ToolRegistry, policy: PolicyEngine) -> None:
        self._registry = registry
        self._policy = policy
        self._logger = get_logger("mcp_proxmox.mcp.server")

    async def handle_message(self, message: dict[str, Any]) -> dict[str, Any] | None:
        """Handle a JSON-RPC request or notification."""

        request_id = message.get("id")
        correlation_id = str(request_id) if request_id is not None else "notification"

        with correlation_context(correlation_id):
            try:
                method = message.get("method")
                if not isinstance(method, str):
                    raise McpProtocolError(-32600, "Missing JSON-RPC method")

                params = message.get("params", {})
                if params is None:
                    params = {}
                if not isinstance(params, dict):
                    raise McpProtocolError(-32602, "Request params must be an object")

                result = await self._dispatch(method, params)
                if request_id is None:
                    return None

                return {
                    "jsonrpc": JSON_RPC_VERSION,
                    "id": request_id,
                    "result": result,
                }
            except McpProtocolError as exc:
                self._logger.warning(
                    "protocol_error", extra={"code": exc.code, "message": exc.message}
                )
                if request_id is None:
                    return None
                return self._error_response(request_id, exc.code, exc.message)
            except PolicyDenied as exc:
                self._logger.warning("policy_denied", extra={"message": str(exc)})
                if request_id is None:
                    return None
                return self._error_response(request_id, -32603, str(exc))
            except Exception as exc:  # pragma: no cover - defensive boundary
                self._logger.exception("internal_error")
                if request_id is None:
                    return None
                return self._error_response(request_id, -32603, str(exc))

    async def _dispatch(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if method == "initialize":
            return self._handle_initialize(params)
        if method == "notifications/initialized":
            return {}
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"tools": [tool.descriptor() for tool in self._registry.list_tools()]}
        if method == "tools/call":
            return await self._handle_tool_call(params)
        raise McpProtocolError(-32601, f"Method not found: {method}")

    def _handle_initialize(self, params: dict[str, Any]) -> dict[str, Any]:
        protocol_version = params.get("protocolVersion", DEFAULT_PROTOCOL_VERSION)
        if not isinstance(protocol_version, str):
            raise McpProtocolError(-32602, "protocolVersion must be a string")

        return {
            "protocolVersion": protocol_version,
            "capabilities": {
                "tools": {
                    "listChanged": False,
                }
            },
            "serverInfo": {
                "name": "mcp-proxmox",
                "version": "0.1.0-alpha.0",
            },
        }

    async def _handle_tool_call(self, params: dict[str, Any]) -> dict[str, Any]:
        tool_name = params.get("name")
        if not isinstance(tool_name, str) or not tool_name:
            raise McpProtocolError(-32602, "tools/call requires a tool name")

        arguments = params.get("arguments", {})
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise McpProtocolError(-32602, "tools/call arguments must be an object")

        tool = self._registry.get_tool(tool_name)
        if tool is None:
            raise McpProtocolError(-32601, f"Unknown tool: {tool_name}")

        self._policy.authorize(tool.policy)
        result = await tool.handler(arguments)
        text = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self._logger.info("tool_call", extra={"tool": tool.name, "outcome": "ok"})

        return {
            "content": [
                {
                    "type": "text",
                    "text": text,
                }
            ],
        }

    def _error_response(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {
            "jsonrpc": JSON_RPC_VERSION,
            "id": request_id,
            "error": {
                "code": code,
                "message": message,
            },
        }
