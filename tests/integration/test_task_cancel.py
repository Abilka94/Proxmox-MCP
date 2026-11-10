from __future__ import annotations

import json

import httpx
import pytest

from mcp_proxmox.config import parse_config
from mcp_proxmox.mcp.handlers import MinimalMcpServer
from mcp_proxmox.mcp.registry import create_default_registry
from mcp_proxmox.policy import PolicyEngine, ToolTier
from mcp_proxmox.pve.auth.config import auth_config_from_app_config
from mcp_proxmox.pve.client.core import PveClient

UPID = "UPID:pve1:00000001:00000001:00000001:test::user@pve!token:"


@pytest.mark.parametrize(
    "scenario",
    [
        "accepted",
        "terminal",
        "preflight",
        "observe",
        "unknown",
        "denied",
        "invalid",
        "extra",
        "race",
        "rejected",
        "not_sent",
        "unknown_wait",
        "preflight_transport",
        "missing_data",
        "null_data",
        "list_data",
        "missing_status",
        "invalid_status",
        "broken_json",
    ],
)
async def test_mcp_through_real_client_mock_transport(scenario):
    config = parse_config(
        {
            "connection": {
                "id": "test",
                "host": "https://pve.invalid",
                "token_id": "user@pve!token",
                "token_secret": "secret",
                "verify_ssl": True,
            },
            "policy": {"mode": "READ_ONLY" if scenario == "denied" else "OPERATOR"},
        }
    )
    requests = []
    delete_url = (
        "https://pve.invalid/api2/json/nodes/pve1/tasks/"
        "UPID%3Apve1%3A00000001%3A00000001%3A00000001%3Atest%3A%3Auser%40pve%21token%3A"
    )
    get_url = delete_url + "/status"
    malformed = {
        "missing_data": b"{}",
        "null_data": b'{"data":null}',
        "list_data": b'{"data":[]}',
        "missing_status": b'{"data":{}}',
        "invalid_status": b'{"data":{"status":"invalid"}}',
        "broken_json": b"broken",
    }
    no_http = scenario in ("denied", "invalid", "extra")
    sequence = [] if no_http else ["GET"]
    if (
        not no_http
        and scenario not in ("preflight", "preflight_transport")
        and scenario not in malformed
    ):
        sequence += ["DELETE"]
        if scenario in ("terminal", "observe"):
            sequence += ["GET"]

    def handler(request):
        index = len(requests)
        assert index < len(sequence), "Лишний HTTP-запрос"
        assert request.method == sequence[index], "Неверный порядок HTTP"
        expected_url = delete_url if request.method == "DELETE" else get_url
        assert str(request.url) == expected_url, "Неверный полный URL"
        assert request.url.scheme == "https" and request.url.host == "pve.invalid"
        assert request.url.query == b"" and request.content == b""
        requests.append(request)
        if scenario in malformed:
            return httpx.Response(200, content=malformed[scenario])
        if scenario == "preflight_transport":
            raise httpx.ConnectError("secret", request=request)
        if request.method == "DELETE":
            if scenario in ("unknown", "unknown_wait"):
                raise httpx.ReadTimeout("secret", request=request)
            if scenario == "not_sent":
                raise httpx.ConnectError("secret", request=request)
            if scenario == "rejected":
                return httpx.Response(401)
            if scenario == "race":
                return httpx.Response(400)
            return httpx.Response(200, json={"data": None})
        if scenario == "preflight" or scenario == "observe" and len(requests) > 2:
            return httpx.Response(403)
        return httpx.Response(
            200,
            json={
                "data": {
                    "status": "stopped"
                    if scenario == "terminal" and len(requests) > 2
                    else "running",
                    "exitstatus": "OK",
                }
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        registry = create_default_registry(
            config, PveClient(auth_config_from_app_config(config), client=http)
        )
        tool = registry.get_tool("task_cancel")
        assert tool.policy.tier == ToolTier.OPERATOR
        assert tool.input_schema["properties"]["timeout"]["maximum"] == 3600
        assert tool.input_schema["properties"]["poll_interval"]["minimum"] == 0.1
        args = {
            "upid": UPID,
            "node": "pve1",
            "wait": scenario in ("terminal", "observe", "unknown_wait", "not_sent", "rejected"),
        }
        if scenario == "invalid":
            args["timeout"] = 0
        if scenario == "extra":
            args["tier"] = "READ"
        server = MinimalMcpServer(registry, PolicyEngine(config.policy))
        response = await server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "task_cancel", "arguments": args},
            }
        )
    assert [r.method for r in requests] == sequence
    if scenario in ("denied", "invalid", "extra"):
        assert response["error"]["code"] == (-32603 if scenario == "denied" else -32602)
        assert not requests
        return
    result = json.loads(response["result"]["content"][0]["text"])
    assert "secret" not in json.dumps(result)
    assert set(result) == {
        "upid",
        "node",
        "cancel_requested",
        "status",
        "stopped",
        "exitstatus",
        "timed_out",
        "error",
        "message",
        "wait_seconds",
    }
    assert all("/cluster/" not in str(r.url) for r in requests)
    if scenario in malformed or scenario == "preflight_transport":
        assert len(requests) == 1 and result["cancel_requested"] is False
        assert result["error"]["code"] == (
            "transport_error" if scenario == "preflight_transport" else "invalid_response"
        )
    elif scenario == "preflight":
        assert len(requests) == 1 and result["cancel_requested"] is False
    elif scenario in ("unknown", "unknown_wait"):
        assert len(requests) == 2 and result["cancel_requested"] is None
    elif scenario == "observe":
        assert result["cancel_requested"] is True and result["stopped"] is None
        assert result["error"]["code"] == "observation_failed"
    elif scenario == "terminal":
        assert result["stopped"] is True and result["exitstatus"] == "OK"
    elif scenario in ("race", "rejected", "not_sent"):
        assert result["cancel_requested"] is False and result["stopped"] is None
    else:
        assert len(requests) == 2 and result["status"] == "unknown"


@pytest.mark.parametrize("status", [200, 202])
@pytest.mark.parametrize("wait", [False, True])
async def test_mcp_non_null_delete_preserves_status_without_polling(status, wait):
    config = parse_config(
        {
            "connection": {
                "id": "test",
                "host": "https://pve.invalid",
                "token_id": "user@pve!token",
                "token_secret": "secret",
            },
            "policy": {"mode": "OPERATOR"},
        }
    )
    calls = []
    task_url = (
        "https://pve.invalid/api2/json/nodes/pve1/tasks/"
        "UPID%3Apve1%3A00000001%3A00000001%3A00000001%3Atest%3A%3Auser%40pve%21token%3A"
    )

    def handler(request):
        index = len(calls)
        assert index < 2
        assert request.method == ("GET" if index == 0 else "DELETE")
        assert str(request.url) == task_url + ("/status" if index == 0 else "")
        assert request.content == b"" and request.url.query == b""
        calls.append(request)
        return (
            httpx.Response(200, json={"data": {"status": "running"}})
            if index == 0
            else httpx.Response(status, json={"data": {"private": "synthetic-response-content"}})
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        server = MinimalMcpServer(
            create_default_registry(
                config, PveClient(auth_config_from_app_config(config), client=http)
            ),
            PolicyEngine(config.policy),
        )
        response = await server.handle_message(
            {
                "jsonrpc": "2.0",
                "id": "fa04",
                "method": "tools/call",
                "params": {
                    "name": "task_cancel",
                    "arguments": {"upid": UPID, "node": "pve1", "wait": wait},
                },
            }
        )
    result = json.loads(response["result"]["content"][0]["text"])
    assert len(calls) == 2
    assert result["cancel_requested"] is None and result["stopped"] is None
    assert result["status"] == "unknown" and result["timed_out"] is False
    assert result["error"]["code"] == "request_outcome_unknown"
    assert result["error"]["phase"] == "delete"
    assert result["error"]["http_status"] == status
    assert result["wait_seconds"] == 0
    assert "synthetic-response-content" not in json.dumps(response)


@pytest.mark.parametrize(
    "scenario,wait", [("completed", False), ("completed", True), ("cancel_then_read", False)]
)
async def test_mcp_completed_and_no_wait_read_repeat(scenario, wait):
    config = parse_config(
        {
            "connection": {
                "id": "test",
                "host": "https://pve.invalid",
                "token_id": "user@pve!token",
                "token_secret": "secret",
            },
            "policy": {"mode": "OPERATOR"},
        }
    )
    calls = []
    expected = ["GET", "GET"] if scenario == "completed" else ["GET", "DELETE", "GET", "GET"]
    task_url = (
        "https://pve.invalid/api2/json/nodes/pve1/tasks/"
        "UPID%3Apve1%3A00000001%3A00000001%3A00000001%3Atest%3A%3Auser%40pve%21token%3A"
    )

    def handler(request):
        index = len(calls)
        assert index < len(expected) and request.method == expected[index]
        assert str(request.url) == task_url + ("" if request.method == "DELETE" else "/status")
        assert request.content == b"" and request.url.query == b""
        calls.append(request)
        if request.method == "DELETE":
            return httpx.Response(200, json={"data": None})
        running = scenario == "cancel_then_read" and index == 0
        return httpx.Response(
            200,
            json={"data": {"status": "running" if running else "stopped", "exitstatus": "OK"}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        client = PveClient(auth_config_from_app_config(config), client=http)
        server = MinimalMcpServer(
            create_default_registry(config, client), PolicyEngine(config.policy)
        )

        async def call(request_id):
            response = await server.handle_message(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": "task_cancel",
                        "arguments": {"upid": UPID, "node": "pve1", "wait": wait},
                    },
                }
            )
            return json.loads(response["result"]["content"][0]["text"])

        first = await call(1)
        if scenario == "cancel_then_read":
            assert len(calls) == 2
            assert first["cancel_requested"] is True
            assert first["status"] == "unknown" and first["stopped"] is None
            observed = await client.get_task_status_on_node("pve1", UPID)
            assert observed.status == "stopped" and observed.exitstatus == "OK"
        else:
            assert first["cancel_requested"] is False and first["stopped"] is True
        repeated = await call(2)

    assert [r.method for r in calls] == expected
    assert repeated["cancel_requested"] is False and repeated["stopped"] is True
    assert repeated["status"] == "stopped" and repeated["exitstatus"] == "OK"
    assert repeated["error"] is None and repeated["timed_out"] is False
