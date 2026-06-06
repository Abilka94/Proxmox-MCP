# Technical Debt Remediation Report

**Date:** 2026-06-04  
**Context:** Technical sprint to fix 3 priority issues identified in INDEPENDENT_PROJECT_REVIEW.md, executed after initial Phase 1A implementation.

---

## Issues Fixed

### 1. MCP Protocol Spec Compliance

**Problem:** `tools/call` responses contained non-standard `structuredContent` and `isError` fields, violating MCP protocol 2024-11-05.

**Fix:**
| File | Change |
|------|--------|
| `src/mcp_proxmox/mcp/handlers/server.py` | Removed `structuredContent` and `isError` from `_handle_tool_call` response. Returns only `{"content": [{"type": "text", "text": json.dumps(result)}]}`. Made all handler methods `async def`. |
| `src/mcp_proxmox/mcp/registry/tools.py` | Changed `ToolHandler` type from `Callable[..., dict]` to `Callable[..., Awaitable[dict]]`. Made `server_info` and `list_nodes_tool` handlers `async def`. |
| `tests/unit/test_mcp_server.py` | Updated all assertions: check `content[0]["text"]` instead of `structuredContent`. Changed to `IsolatedAsyncioTestCase`. Made `FakePveClient.get_nodes` async. |

### 2. PVE Client — Replace urllib with httpx Async

**Problem:** `pve/client/core.py` used `urllib.request` (blocking, no async, no connection pooling). Architecture requires httpx async.

**Fix:**
| File | Change |
|------|--------|
| `src/mcp_proxmox/pve/client/core.py` | Replaced all urllib imports with httpx. `SupportsOpen` protocol → `httpx.AsyncClient | None`. `get_cluster_status`/`get_nodes`/`get_node` now `async def`. `_get_json` uses `client.get(...)` with httpx error handling (`HTTPStatusError`, `RequestError`, `TimeoutException`). `_make_client` constructs `httpx.AsyncClient(verify=..., timeout=...)`. |
| `tests/unit/test_pve_client.py` | Removed `RecordingOpener`/`ErrorOpener`/`FakeResponse`. Uses `httpx.MockTransport` for request mocking. Changed to `IsolatedAsyncioTestCase`. Added `test_auth_header_is_sent` to verify header injection. |

### 3. Documentation Remediation

**Problem:** Outdated docs (`CODEBASE_AUDIT_REPORT.md`, `PHASE_1A_PROGRESS_REPORT.md`) reference old architecture (urllib, stub entry point, 12 tests).

**Fix:**
| File | Change |
|------|--------|
| `CODEBASE_AUDIT_REPORT.md` | Added SUPERSEDED banner noting async/httpx/MCP-spec sprint changes. |
| `docs/implementation/PHASE_1A_PROGRESS_REPORT.md` | Added SUPERSEDED banner noting current state. |

---

## Supporting Changes (Async Chain)

Converting the call chain to async required updating all intermediate layers:

| File | Change |
|------|--------|
| `src/mcp_proxmox/mcp/transport/stdio.py` | `serve_forever`, `read_message`, `write_message` now `async def`. Blocking I/O wrapped with `asyncio.to_thread`. |
| `src/mcp_proxmox/__main__.py` | `main` is now `async def`. Added `cli()` sync wrapper for entry point. Uses `asyncio.run(main())`. |
| `src/mcp_proxmox/domains/nodes/service.py` | `list_nodes` now `async def`. Calls `await client.get_nodes()`. |
| `pyproject.toml` | `requires-python` widened from `<3.14` to `<3.15`. Entry point updated from `:main` to `:cli`. |

---

## Test Results

```
25 passed in 1.64s
```

All original tests preserved and updated for new async/spec-compliant behavior.

---

## Current Component Readiness (Updated)

| Component | Readiness | Notes |
|-----------|-----------|-------|
| Config System | 65% | Unchanged |
| Logging | 45% | Unchanged |
| Policy Engine | 55% | Unchanged |
| MCP Server | 70% | Working stdio server, spec-compliant `tools/call`, tool registry with `list_tools` |
| PVE Client | 60% | Working async httpx client, 3 read methods, error handling, mock testing |
| Orchestrator | 0% | Unchanged |
| Domains | 15% | Node domain has working `list_nodes`; cluster/LXC/VM still skeleton |
| Audit | 0% | Unchanged |
| Cache | 0% | Unchanged |
| Tests | 40% | 25 unit tests; MCP + PVE now covered |
| Deploy | 15% | Unchanged |
| Documentation | 80% | Outdated reports marked SUPERSEDED |

---

## Remaining Debt

1. **Python 3.14 compatibility** — `pytest-asyncio` emits `DeprecationWarning` for `asyncio.get_event_loop_policy()` slated for removal in 3.16. Non-blocking for now.
2. **No async client lifecycle** — `PveClient` creates a new `AsyncClient` per request when no client is injected. Should reuse a long-lived client in production.
3. **`httpx.URL(node_name).path` in `get_node`** — used for safe URL encoding; verify edge cases with special characters in node names.
4. **Entry point uses `asyncio.run()`** — correct for stdio, but `uvicorn`/`MCP SDK` may require different event loop setup in future phases.
