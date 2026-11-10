from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest

from mcp_proxmox.config.models import PolicyConfig, PolicyMode
from mcp_proxmox.domains.tasks.service import task_cancel
from mcp_proxmox.policy import PolicyDenied, PolicyEngine, ToolPolicy, ToolTier
from mcp_proxmox.pve.auth.config import PveAuthConfig
from mcp_proxmox.pve.client.core import PveApiError, PveClient
from mcp_proxmox.pve.client.task_validation import TaskCancelInputError
from mcp_proxmox.pve.models.responses import TaskStatus

UPID = "UPID:pve1:00000001:000000001:00000001:test::user@pve!token:"
AUTH = PveAuthConfig("https://pve.invalid", "user@pve!token", "secret", True, 1)


def fake(status="running"):
    class Client:
        get_task_status_on_node = AsyncMock(return_value=TaskStatus(status=status))
        stop_task = AsyncMock(return_value=None)

    return Client()


@pytest.mark.parametrize("code", [400, 401, 403, 404, 501, 500, None])
async def test_preflight_error_never_deletes(code):
    c = fake()
    c.get_task_status_on_node.side_effect = PveApiError("secret", "/mock", code)
    r = await task_cancel(c, UPID, node="pve1")
    assert r["cancel_requested"] is False and r["status"] == "unknown"
    assert r["stopped"] is None and r["error"]["phase"] == "preflight"
    assert "secret" not in json.dumps(r)
    c.stop_task.assert_not_awaited()


async def test_completed_and_repeat():
    c = fake("stopped")
    c.get_task_status_on_node.return_value.exitstatus = "OK"
    for _ in range(2):
        r = await task_cancel(c, UPID, node="pve1")
        assert r["cancel_requested"] is False and r["stopped"] is True
        assert r["exitstatus"] == "OK"
    c.stop_task.assert_not_awaited()


async def test_no_wait_and_repeated_running():
    c = fake()
    for _ in range(2):
        r = await task_cancel(c, UPID, node="pve1")
        assert r["cancel_requested"] is True and r["stopped"] is None
        assert r["status"] == "unknown"
    assert c.stop_task.await_count == 2 and c.get_task_status_on_node.await_count == 2


@pytest.mark.parametrize("exitstatus", ["OK", "interrupted", "ERROR"])
async def test_terminal_does_not_claim_cancellation(exitstatus):
    c = fake()
    c.get_task_status_on_node.side_effect = [
        TaskStatus(status="running"),
        TaskStatus(status="stopped", exitstatus=exitstatus),
    ]
    r = await task_cancel(c, UPID, node="pve1", wait=True)
    assert r["stopped"] is True and r["cancel_requested"] is True
    assert r["exitstatus"] == exitstatus and "причина не установлена" in r["message"]


@pytest.mark.parametrize("code", [400, 401, 403, 404, 501, 500, None])
async def test_observation_failure_not_success(code):
    c = fake()
    c.get_task_status_on_node.side_effect = [
        TaskStatus(status="running"),
        PveApiError("failure", "/mock", code),
    ]
    r = await task_cancel(c, UPID, node="pve1", wait=True)
    assert r["cancel_requested"] is True and r["stopped"] is None
    assert r["error"]["code"] == "observation_failed"
    assert r["error"]["http_status"] == code


@pytest.mark.parametrize(
    "outcome,expected", [("not_sent", False), ("rejected", False), ("unknown", None), (None, None)]
)
async def test_delete_outcomes(outcome, expected):
    c = fake()
    c.stop_task.side_effect = PveApiError("failure", "/mock", request_outcome=outcome)
    r = await task_cancel(c, UPID, node="pve1", wait=True)
    assert r["cancel_requested"] is expected and r["stopped"] is None
    assert c.get_task_status_on_node.await_count == 1


async def test_timeout_preserves_last_observation():
    c = fake()
    r = await task_cancel(c, UPID, node="pve1", wait=True, timeout=1, poll_interval=30)
    assert r["timed_out"] and r["cancel_requested"] is True
    assert r["status"] == "running" and r["stopped"] is False
    assert r["wait_seconds"] < 1.5


async def test_deadline_bounds_get_and_discards_late_status():
    c = fake()

    async def slow(*args):
        await asyncio.sleep(2)
        return TaskStatus(status="stopped")

    c.stop_task.side_effect = lambda *args: setattr(c.get_task_status_on_node, "side_effect", slow)
    r = await task_cancel(c, UPID, node="pve1", wait=True, timeout=1)
    assert r["timed_out"] and r["status"] == "unknown" and r["stopped"] is None


async def test_coroutine_cancellation_propagates():
    c = fake()
    c.get_task_status_on_node.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await task_cancel(c, UPID, node="pve1")


@pytest.mark.parametrize(
    "arguments",
    [
        dict(upid="encoded%3A"),
        dict(node="other"),
        dict(node="../pve1"),
        dict(wait="false"),
        dict(timeout=True),
        dict(timeout=0),
        dict(timeout=3601),
        dict(timeout="120"),
        dict(poll_interval=True),
        dict(poll_interval=float("nan")),
        dict(poll_interval=float("inf")),
        dict(poll_interval=0),
        dict(poll_interval=31),
    ],
)
async def test_validation_before_http(arguments):
    c = fake()
    args = dict(upid=UPID, node="pve1") | arguments
    with pytest.raises(TaskCancelInputError):
        await task_cancel(c, **args)
    c.stop_task.assert_not_awaited()
    c.get_task_status_on_node.assert_not_awaited()


@pytest.mark.parametrize("code", [400, 401, 403, 404, 501, 500, 302])
async def test_client_http_outcome_no_retry(code):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(code, headers={"Location": "https://elsewhere.invalid"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(PveApiError) as error:
            await PveClient(AUTH, client=http).stop_task("pve1", UPID)
    assert len(calls) == 1
    assert error.value.status_code == code
    assert error.value.request_outcome == (
        "rejected" if code < 500 and code >= 400 or code == 501 else "unknown"
    )


@pytest.mark.parametrize(
    "exc,outcome",
    [
        (httpx.ConnectError, "not_sent"),
        (httpx.ConnectTimeout, "not_sent"),
        (httpx.PoolTimeout, "not_sent"),
        (httpx.ReadTimeout, "unknown"),
        (httpx.WriteTimeout, "unknown"),
        (httpx.ReadError, "unknown"),
        (httpx.WriteError, "unknown"),
        (httpx.RemoteProtocolError, "unknown"),
    ],
)
async def test_client_transport(exc, outcome):
    calls = []

    def handler(request):
        calls.append(request)
        raise exc("secret", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(PveApiError) as error:
            await PveClient(AUTH, client=http).stop_task("pve1", UPID)
    assert error.value.request_outcome == outcome and len(calls) == 1
    assert "secret" not in str(error.value)


@pytest.mark.parametrize("body", [None, {}, {"data": 123}, {"data": []}])
async def test_invalid_success_response(body):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=body))
    ) as http:
        with pytest.raises(PveApiError) as error:
            await PveClient(AUTH, client=http).stop_task("pve1", UPID)
    assert error.value.request_outcome == "unknown"


@pytest.mark.parametrize("status", [200, 202, 206])
@pytest.mark.parametrize("payload", [123, [], {"private": "synthetic-response-content"}])
async def test_non_null_payload_preserves_http_status(status, payload, caplog):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, json={"data": payload})

    with caplog.at_level("INFO"):
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
            with pytest.raises(PveApiError) as error:
                await PveClient(AUTH, client=http).stop_task("pve1", UPID)

    assert error.value.status_code == status
    assert error.value.kind == "invalid_response"
    assert error.value.request_outcome == "unknown"
    assert len(calls) == 1 and calls[0].method == "DELETE"
    events = [r for r in caplog.records if r.getMessage() == "pve_delete"]
    assert len(events) == 1
    assert events[0].http_status == status
    assert events[0].request_outcome == "unknown"
    assert events[0].kind == "invalid_response"
    assert "synthetic-response-content" not in str(error.value)
    assert "synthetic-response-content" not in caplog.text


@pytest.mark.parametrize("status,body", [(200, b""), (204, b""), (200, b"not json")])
async def test_empty_or_malformed_is_unknown(status, body):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(status, content=body))
    ) as http:
        with pytest.raises(PveApiError) as error:
            await PveClient(AUTH, client=http).stop_task("pve1", UPID)
    assert error.value.kind == "invalid_response"
    assert error.value.request_outcome == "unknown"


@pytest.mark.parametrize(
    "special,encoded",
    [
        (False, "UPID%3Apve1%3A00000001%3A000000001%3A00000001%3Atest%3A%3Auser%40pve%21token%3A"),
        (
            True,
            "UPID%3Apve1%3A00000001%3A000000001%3A00000001%3Atest%3A%25%3F%23%3Auser%40pve%21token%3A",
        ),
    ],
)
async def test_url_auth_encoding_and_null_success(special, encoded):
    upid = UPID.replace("test::", "test:%?#:") if special else UPID
    calls = []

    def handler(r):
        calls.append(r)
        assert r.method == "DELETE" and r.content == b""
        assert r.url.scheme == "https" and r.url.host == "pve.invalid"
        assert str(r.url) == "https://pve.invalid/api2/json/nodes/pve1/tasks/" + encoded
        assert r.url.raw_path == ("/api2/json/nodes/pve1/tasks/" + encoded).encode()
        assert r.url.query == b""
        assert r.headers["Authorization"] == "PVEAPIToken=user@pve!token=secret"
        return httpx.Response(200, json={"data": None, "metadata": True})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        assert await PveClient(AUTH, client=http).stop_task("pve1", upid) is None
        assert not http.is_closed
    assert len(calls) == 1


@pytest.mark.parametrize("payload", [None, [], {"key": 1}])
async def test_generic_delete_payload(payload):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"data": payload}))
    ) as http:
        assert await PveClient(AUTH, client=http)._delete_json("/test") == payload


@pytest.mark.parametrize(
    "mode,tier,allowed",
    [
        (
            mode,
            tier,
            tier == ToolTier.READ or mode == PolicyMode.OPERATOR and tier == ToolTier.OPERATOR,
        )
        for mode in PolicyMode
        for tier in ToolTier
    ],
)
def test_policy_matrix(mode, tier, allowed):
    engine = PolicyEngine(PolicyConfig(mode=mode))
    policy = ToolPolicy("test", tier)
    if allowed:
        engine.authorize(policy)
    else:
        with pytest.raises(PolicyDenied):
            engine.authorize(policy)


def test_schema_modes_and_default():
    schema = json.loads(Path("config/schema/config.schema.json").read_text())
    mode = schema["properties"]["policy"]["properties"]["mode"]
    assert set(mode["enum"]) == {m.value for m in PolicyMode}
    assert PolicyConfig().mode == mode["default"] == "READ_ONLY"


@pytest.mark.parametrize("status", ["unexpected", ""])
async def test_invalid_status_blocks_delete(status):
    c = fake(status)
    r = await task_cancel(c, UPID, node="pve1")
    assert r["error"]["code"] == "invalid_response"
    assert r["stopped"] is None
    c.stop_task.assert_not_awaited()


@pytest.mark.parametrize("payload", [{}, {"status": "unexpected"}, [], None])
async def test_nodal_status_invalid_payload(payload):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"data": payload}))
    ) as http:
        with pytest.raises(PveApiError):
            await PveClient(AUTH, client=http).get_task_status_on_node("pve1", UPID)


async def test_owned_clients_closed_and_injected_client_kept_open(monkeypatch):
    clients = []

    def make(self):
        http = httpx.AsyncClient(
            transport=httpx.MockTransport(
                lambda r: (
                    httpx.Response(200, json={"data": {"status": "running"}})
                    if r.method == "GET"
                    else httpx.Response(200, json={"data": None})
                )
            )
        )
        clients.append(http)
        return http

    monkeypatch.setattr(PveClient, "_make_client", make)
    c = PveClient(AUTH)
    await c.stop_task("pve1", UPID)
    await c.get_task_status_on_node("pve1", UPID)
    await c._post_json("/test")
    assert len(clients) == 3 and all(h.is_closed for h in clients)


async def test_logs_preserve_facts_without_secret(caplog):
    from mcp_proxmox.logging import correlation_context

    c = fake()
    c.get_task_status_on_node.side_effect = [
        TaskStatus(status="running"),
        PveApiError("secret", "/mock", 403),
    ]
    with caplog.at_level("INFO"), correlation_context("cancel-test"):
        await task_cancel(c, UPID, node="pve1", wait=True)
    records = [r for r in caplog.records if r.name == "mcp_proxmox.task_cancel"]
    assert records and records[-1].phase == "observe"
    assert records[-1].request_outcome is True and records[-1].status == "unknown"
    assert "secret" not in str([r.__dict__ for r in records])


def test_unknown_policy_denied():
    config = PolicyConfig.model_construct(mode="UNKNOWN")
    with pytest.raises(PolicyDenied):
        PolicyEngine(config).authorize(ToolPolicy("test", ToolTier.READ))
    with pytest.raises(ValueError):
        PolicyConfig(mode="UNKNOWN")


@pytest.mark.parametrize("status,body", [(200, b"broken"), (200, b"{}")])
async def test_post_invalid_response_is_structured(status, body):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(status, content=body))
    ) as http:
        with pytest.raises(PveApiError):
            await PveClient(AUTH, client=http)._post_json("/test")


@pytest.mark.parametrize(
    "body",
    [
        b"{}",
        b'{"data":null}',
        b'{"data":[]}',
        b'{"data":{}}',
        b'{"data":{"status":"invalid"}}',
        b"broken",
    ],
)
async def test_malformed_preflight_normalized(body):
    calls = []

    def handler(r):
        calls.append(r.method)
        assert r.method == "GET"
        return httpx.Response(200, content=body)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        result = await task_cancel(PveClient(AUTH, client=http), UPID, node="pve1")
    assert calls == ["GET"]
    assert result["error"]["code"] == "invalid_response"
    assert result["error"]["phase"] == "preflight"
    assert result["error"]["http_status"] == 200
    assert result["cancel_requested"] is False


@pytest.mark.parametrize(
    "failure,expected,http_status,kind",
    [
        (None, "accepted", 200, None),
        (401, "rejected", 401, "authentication_failed"),
        (httpx.ConnectError, "not_sent", None, "transport_not_sent"),
        (httpx.ReadTimeout, "unknown", None, "transport_error"),
    ],
)
async def test_delete_json_log(failure, expected, http_status, kind):
    import io
    import logging

    from mcp_proxmox.logging import correlation_context
    from mcp_proxmox.logging.setup import JsonFormatter

    stream = io.StringIO()
    logger = logging.getLogger("mcp_proxmox.pve.client")
    old = logger.handlers[:], logger.level, logger.propagate
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.handlers, logger.propagate = [handler], False
    logger.setLevel(logging.INFO)

    def transport(r):
        if isinstance(failure, type):
            raise failure("raw-secret", request=r)
        return httpx.Response(failure or 200, json={"data": None, "secret": "raw-secret"})

    try:
        with correlation_context("fr03-test"):
            async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
                if failure is None:
                    await PveClient(AUTH, client=http).stop_task("pve1", UPID)
                else:
                    with pytest.raises(PveApiError):
                        await PveClient(AUTH, client=http).stop_task("pve1", UPID)
    finally:
        logger.handlers, logger.level, logger.propagate = old
    events = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert len(events) == 1
    event = events[0]
    assert event["event"] == "pve_delete" and event["phase"] == "delete"
    assert event["request_outcome"] == expected and event["http_status"] == http_status
    assert event["kind"] == kind and event["correlation_id"] == "fr03-test"
    assert "raw-secret" not in stream.getvalue()
    assert "Authorization" not in stream.getvalue()
