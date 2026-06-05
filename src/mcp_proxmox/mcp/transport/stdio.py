"""Minimal stdio transport using LSP-style content framing. Async."""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, BinaryIO

from mcp_proxmox.logging import get_logger
from mcp_proxmox.mcp.handlers.server import MinimalMcpServer


class StdioTransport:
    """Read and write JSON-RPC messages over stdio."""

    def __init__(
        self,
        server: MinimalMcpServer,
        *,
        stdin: BinaryIO | None = None,
        stdout: BinaryIO | None = None,
    ) -> None:
        self._server = server
        self._stdin = stdin or sys.stdin.buffer
        self._stdout = stdout or sys.stdout.buffer
        self._logger = get_logger("mcp_proxmox.mcp.stdio")

    async def serve_forever(self) -> int:
        """Serve until stdin reaches EOF."""

        while True:
            message = await self.read_message()
            if message is None:
                return 0
            response = await self._server.handle_message(message)
            if response is not None:
                await self.write_message(response)

    async def read_message(self) -> dict[str, Any] | None:
        content_length: int | None = None

        while True:
            raw_line = await asyncio.to_thread(self._stdin.readline)
            if raw_line == b"":
                return None

            line = raw_line.decode("ascii").strip()
            if not line:
                break

            name, _, value = line.partition(":")
            if name.lower() == "content-length":
                content_length = int(value.strip())

        if content_length is None:
            raise RuntimeError("Missing Content-Length header")

        body = await asyncio.to_thread(self._stdin.read, content_length)
        if len(body) != content_length:
            raise RuntimeError("Unexpected EOF while reading request body")

        message = json.loads(body.decode("utf-8"))
        if not isinstance(message, dict):
            raise RuntimeError("JSON-RPC payload must be an object")
        self._logger.info("message_received", extra={"method": message.get("method")})
        return message

    async def write_message(self, message: dict[str, Any]) -> None:
        body = json.dumps(message, ensure_ascii=False).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        self._stdout.write(header)
        self._stdout.write(body)
        self._stdout.flush()
        self._logger.info("message_sent")
