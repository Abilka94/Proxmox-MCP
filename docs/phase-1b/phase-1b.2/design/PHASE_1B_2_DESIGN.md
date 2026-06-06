# Phase 1B.2 — Task Domain Extended Design

**Date:** 2026-06-06
**Status:** Approved — ready for implementation
**Primary Target:** Proxmox VE 9.x
**Secondary Target:** Proxmox VE 8.x (best effort)

---

## 1. Goal

Complete the READ lifecycle for Proxmox tasks by adding two polling tools:

- **task_wait** — block until a task reaches `status == "stopped"`, then return its final status
- **task_follow** — block until a task completes, accumulating its full log, then return status + log

Both tools build on the existing `task_status` and `task_log` from Phase 1B.1. No new PVE endpoints, no new PVE client methods, and no POST operations.

---

## 2. Tool: `task_wait`

### Purpose

Allow an LLM or automation script to submit an asynchronous PVE operation (e.g. create a VM via a future `vm_create` tool) and then block until the worker task finishes, without manually polling `task_status` in a loop.

### Signature

| Property | Value |
|----------|-------|
| **Tier** | READ |
| **Parameters** | `upid` (required), `node` (optional), `timeout` (optional, default 120, max 3600), `poll_interval` (optional, default 1.0, min 0.1, max 30) |
| **Response** | `{ "upid": "...", "status": "stopped", "exitstatus": "OK", "completed": true, "wait_seconds": 3.2 }` |
| **PVE endpoint** | `GET /cluster/tasks/{upid}/status` → fallback `GET /nodes/{node}/tasks/{upid}/status` |

### Algorithm

```
1. Call task_status(upid, node=node)
2. If status == "stopped":
       return { upid, status, exitstatus, completed: true, wait_seconds: elapsed }
3. If elapsed >= timeout:
        return { upid, status, completed: false, timed_out: true, wait_seconds: timeout }
4. Sleep for poll_interval seconds
5. Go to step 1
```

### Parameters Detail

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `upid` | str | — | — | — | Opaque UPID from any task-producing tool |
| `node` | str | None | — | — | Hint for cluster→node fallback (recommended if known) |
| `timeout` | int | 120 | 1 | 3600 | Maximum seconds to wait for completion |
| `poll_interval` | float | 1.0 | 0.1 | 30.0 | Seconds between status checks |

### Response Shapes

#### Success (completed within timeout)
```json
{
  "upid": "UPID:pve:...",
  "status": "stopped",
  "exitstatus": "OK",
  "completed": true,
  "wait_seconds": 4.7
}
```

#### Timeout (task still running)
```json
{
  "upid": "UPID:pve:...",
  "status": "running",
  "completed": false,
  "timed_out": true,
  "wait_seconds": 120.0
}
```

#### Task disappeared
```json
{
  "upid": "UPID:pve:...",
  "completed": false,
  "error": "task_not_found",
  "wait_seconds": 12.3
}
```

---

## 3. Tool: `task_follow`

### Purpose

Allow an LLM to not only wait for a task but also see its complete log output. This is essential for understanding *why* a task failed (e.g. vzdump error details, qmcreate configuration errors) without making separate `task_log` calls.

### Signature

| Property | Value |
|----------|-------|
| **Tier** | READ |
| **Parameters** | `upid` (required), `node` (required), `timeout` (optional, default 120, max 3600), `poll_interval` (optional, default 1.0, min 0.1, max 30) |
| **Response** | `{ "upid": "...", "status": "stopped", "exitstatus": "OK", "completed": true, "wait_seconds": 3.2, "lines": [...], "total_lines": 15 }` |

### Algorithm

```
1. Call task_status(upid, node=node) to get current status
2. Call task_log(upid, node, start=0) to get initial log
3. If status == "stopped":
       return { upid, status, exitstatus, completed: true, wait_seconds, lines, total_lines }
4. If elapsed >= timeout:
       return { upid, status, completed: false, timed_out: true, wait_seconds, lines, total_lines }
       Note: last known status and all accumulated log lines are preserved in the response
5. Sleep for poll_interval seconds
6. Call task_status(upid, node=node)
7. Call task_log(upid, node, start=last_lineno) — only new lines
8. Append new lines to accumulated log
9. Go to step 3
```

### Parameters Detail

| Parameter | Type | Default | Min | Max | Description |
|-----------|------|---------|-----|-----|-------------|
| `upid` | str | — | — | — | Opaque UPID |
| `node` | str | — | — | — | **Required** — log endpoint requires a node |
| `timeout` | int | 120 | 1 | 3600 | Maximum seconds to wait |
| `poll_interval` | float | 1.0 | 0.1 | 30.0 | Seconds between poll cycles |

### Response Shapes

#### Success with log
```json
{
  "upid": "UPID:pve:000B2E5A:...",
  "status": "stopped",
  "exitstatus": "OK",
  "completed": true,
  "wait_seconds": 12.1,
  "lines": [
    {"text": "running task...", "lineno": 0},
    {"text": " [...] 50%", "lineno": 5},
    {"text": "TASK OK", "lineno": 10}
  ],
  "total_lines": 11
}
```

#### Timeout with partial log
When the timeout is reached, the accumulated log and the last known status are **not discarded** — they are returned as part of the response:

```json
{
  "upid": "UPID:pve:...",
  "status": "running",
  "completed": false,
  "timed_out": true,
  "wait_seconds": 120.0,
  "lines": [
    {"text": "running task...", "lineno": 0},
    {"text": " [...] 30%", "lineno": 3}
  ],
  "total_lines": 4
}
```

#### Task disappeared with partial log
```json
{
  "upid": "UPID:pve:...",
  "completed": false,
  "error": "task_not_found",
  "wait_seconds": 45.0,
  "lines": [...],
  "total_lines": 3
}
```

---

## 4. Key Differences Between `task_wait` and `task_follow`

| Aspect | `task_wait` | `task_follow` |
|--------|-------------|---------------|
| **Node parameter** | Optional (status has fallback) | **Required** (log requires node) |
| **Log output** | No log | Full accumulated log |
| **Poll interval** | 1.0s (status changes slower than log) | 1.0s (same as task_wait; user can lower if needed) |
| **Number of API calls per cycle** | 1 (status) | 2 (status + log) |
| **Use case** | "Did my operation finish?" | "What happened during my operation?" |

---

## 5. MCP Request/Response Constraints

MCP uses JSON-RPC 2.0 with a standard request/response model. Neither Server-Sent Events nor streaming responses are part of the current MCP specification version used by this project.

**Consequence:** Both `task_wait` and `task_follow` are **synchronous from the MCP client's perspective**. The MCP server:

1. Receives the `tools/call` request
2. Enters an `asyncio` polling loop (non-blocking to the event loop via `asyncio.sleep`)
3. Returns a single complete JSON-RPC response when done or on timeout

**Implication for LLM clients:** The LLM will not see intermediate log lines. It will only see the final response. This is acceptable for Phase 1B.2. Future streaming support (if MCP adds it) would be a separate enhancement.

**Timeout is a safety net:** Because MCP HTTP transports (if used in future) may have their own timeouts, the tool's `timeout` parameter must be respected and should default to a value well below common HTTP transport timeouts (typically 120s for HTTP proxies, 600s for WebSocket).

---

## 6. Polling Strategy

| Aspect | `task_wait` | `task_follow` |
|--------|-------------|---------------|
| **Default interval** | 1.0s | 1.0s |
| **Status check** | Every cycle | Every cycle |
| **Log check** | Never | Every cycle (incremental) |
| **Backoff on error** | Yes (exponential, 1× → 2× → 4×, max 30s) | Same |
| **Fast path** | If `status == "stopped"` on first call, return immediately (0 wait) | Same |

### Exponential Backoff on Transient Errors

If `task_status` or `task_log` raises `PveApiError` with a transient status (5xx, connection error), the poll interval is doubled (starting from `poll_interval`, up to max 30s). The counter is reset on the next successful poll. This prevents hammering a struggling PVE API.

If the error is non-transient (4xx, auth error), polling stops immediately and the error is returned.

---

## 7. Timeouts

| Parameter | `task_wait` | `task_follow` | Rationale |
|-----------|-------------|---------------|-----------|
| Default | 120s | 120s | MCP-friendly default; users can raise for long operations (vzdump, migrations) |
| Minimum | 1s | 1s | Sanity check |
| Maximum | 3600s | 3600s | Prevents runaway polling; aligns with ADR-0009 node_request_timeout_sec (30s) per individual call, but overall aggregate can be up to 1h |

**On timeout:** The tool does not raise an error — it returns a well-formed response with `"completed": false` and `"timed_out": true`. The last known `status` and any accumulated log lines (`task_follow`) are preserved in the response. The caller can inspect `status` to see whether the task is still running, and can call `task_status` later for a follow-up.

---

## 8. Poll Intervals

| Scenario | Recommended Interval | Rationale |
|----------|---------------------|-----------|
| Default `task_wait` | 1.0s | Status endpoint is cheap; 1s granularity is sufficient |
| Default `task_follow` | 1.0s | Same as task_wait; reduces API load. User can specify lower interval for faster log updates |
| Long-running tasks (vzdump) | 2.0–5.0s | User can increase interval to reduce API load |
| Rapid tasks (apt update) | 1.0s | User can lower interval if faster response needed |

The `poll_interval` parameter is exposed to the caller. The MCP client can choose the trade-off between responsiveness and API load.

---

## 9. Error Handling

| Error | Behaviour | Response |
|-------|-----------|----------|
| `PveApiError(4xx)` — auth, bad request | Stop polling immediately | Return `{ error: "api_error", detail: "..." }` |
| `PveApiError(5xx)` — server error | Exponential backoff, continue polling | — |
| Connection error (DNS, TCP) | Exponential backoff, continue polling | — |
| UPID not found (status returns 404/501) | Stop polling immediately | `{ error: "task_not_found" }` |
| Timeout exceeded | Return partial result with last known status and accumulated log | `{ completed: false, timed_out: true, ... }` |
| Any unexpected exception | Stop polling immediately | Re-raise as `PveApiError` |

### Transient Error Classification

Transient (retry with backoff): `5xx`, connection errors, DNS failures  
Non-transient (stop): `4xx` (except 408/429), auth errors, invalid UPID

---

## 10. Behaviour When Task Disappears

A task UPID may become unavailable if:

1. PVE's internal task history was rotated out (older tasks are pruned)
2. The UPID was malformed or never existed
3. The node that owned the task was removed from the cluster

When `task_status` returns a 404-like response (or 501 on PVE 8.x cluster-level without node fallback), the tool stops polling and returns `{ "error": "task_not_found" }` with `"completed": false`. For `task_follow`, any log lines accumulated before the disappearance are still included in the response.

**Cross-node note from Phase 1B.1:** On PVE 8.x, `GET /cluster/tasks/{upid}/status` returns 501. If `node` was not provided, the fallback cannot activate. In this case:
- `task_wait` without `node` → immediate `task_not_found` on PVE 8.x
- `task_wait` with `node` → works via node-level status endpoint
- `task_follow` always requires `node` → always works

On PVE 9.x (primary target), the cluster-level endpoint is expected to work, so `task_wait` without `node` should work correctly.

---

## 11. Compatibility: PVE 9.x (Primary) vs PVE 8.x (Secondary)

| Feature | PVE 9.x (Primary) | PVE 8.x (Secondary) |
|---------|-------------------|---------------------|
| `task_wait` without `node` | ✅ Works (cluster-level status) | ⚠️ Returns 501 → `task_not_found` error (must provide `node`) |
| `task_wait` with `node` | ✅ Works | ✅ Works (node-level status) |
| `task_follow` | ✅ Works | ✅ Works (log and status at node level) |
| `poll_interval` | ✅ Works | ✅ Works (no version dependency) |
| `timeout` | ✅ Works | ✅ Works |

**Design decision:** No PVE 8.x–specific code paths. The existing cluster→node fallback from Phase 1B.1 is sufficient. On PVE 9.x the cluster-level endpoint is assumed to work — if it doesn't, the same fallback kicks in.

---

## 12. Use of Existing `task_status`

Both tools call the existing `task_status` domain function (which in turn calls `PveClient.get_task_status` with cluster→node fallback).

No changes to the existing function are needed.

**Mapping from `task_status` response to poll state:**

| `task_status` response field | Poll state |
|------------------------------|------------|
| `"status": "stopped"` | Task complete — return result |
| `"status": "running"` | Continue polling |
| `"status"` absent or `None` | Treat as "running" (backward compatibility with PVE 8.x where `status` may be absent for finished tasks) |

---

## 13. Use of Existing `task_log`

`task_follow` calls the existing `task_log` domain function with incremental `start` offsets.

**Incremental log strategy:**

1. First call: `task_log(upid, node, start=0)` — fetch all lines
2. Track the highest `lineno` seen across all accumulated lines
3. Subsequent calls: `task_log(upid, node, start=highest_lineno + 1)`
4. Append new lines (those with `lineno > last_seen`) to accumulated list

**Edge case — log lines without `lineno`:** If a line has `lineno: null`, it is always appended and treated as a new line. The incremental strategy relies on the presence of line numbers for efficiency; lines without numbers are still captured but may cause duplicates. This matches PVE's actual behaviour (most lines have `n`).

**Line count limit:** To prevent unbounded memory use and excessively large MCP responses, `task_follow` caps accumulated lines at `max_log_lines = 5000` (matching ADR-0009's log max_lines cap). If this cap is reached, polling continues (for status) but further log lines are discarded. The response includes:

- `"log_truncated": true` — explicit flag indicating the log was truncated
- `"total_lines": 5000` — the actual count of accumulated lines (equals the cap)

---

## 14. Load Limitations (ADR-0009 Compliance)

| Constraint | Limitation | Implementation |
|------------|------------|----------------|
| Max concurrent per node | 5 | Each poll cycle uses the existing HTTP client pool; no additional concurrency control needed beyond what PveClient already provides |
| Max concurrent cluster | 15 | Same — PveClient manages its own semaphore |
| Node request timeout | 30s | Each individual `task_status` / `task_log` call respects this timeout; if exceeded, treated as transient error (backoff) |
| Log max_lines | 5000 | `task_follow` caps accumulated lines at 5000; response includes `log_truncated: true` when limit reached |
| Poll overhead | Low | A single `task_wait` or `task_follow` session issues ~status_checks + ~log_checks total API calls. At 1.0s interval for 120s = ~120 API calls default. Acceptable for occasional use. |

**Important:** These tools are designed for **interactive use** (LLM waiting for a single task). They are not intended for bulk monitoring of dozens of tasks simultaneously. The `max_concurrent_cluster: 15` limit from PveClient implicitly limits concurrent polling sessions.

---

## 15. Operator Layer Preparation

Though the Operator Layer is a future concern, the design accounts for it:

| Requirement | How Phase 1B.2 prepares |
|-------------|------------------------|
| Future non-blocking task wait | The polling loop is isolated in `domains/tasks/service.py`. An Operator could call the same domain function but manage its own scheduling |
| Job Store integration | The final response shape (`completed`, `wait_seconds`, `status`, `exitstatus`) is a natural fit for persisting as a job record |
| Memory/Knowledge integration | Task outcome (`UPID → {status, exitstatus, wait_seconds}`) is trivially storable as a Knowledge entity |
| Cancellation | `task_cancel` is not implemented but `task_wait`'s polling loop could be interrupted by a future cancellation signal |

**What remains outside Phase 1B.2:**
- `task_cancel` — POST to `/nodes/{node}/tasks/{upid}/status/stop` → Phase 1C
- `task_stop` — synonym or alias → Phase 1C
- Any POST operations → Phase 1C+
- Operator Mode (background task orchestration) → Phase 2+
- Job Store (persistent task history in SQLite) → Phase 2+
- Memory Layer integration (Knowledge entities for tasks) → Phase 3+

---

## 16. Out of Scope (Reminder)

The following are explicitly **not** part of Phase 1B.2:

- `task_cancel` / `task_stop`
- Any POST operations
- Server-Sent Events or WebSocket streaming
- Operator Mode
- Job Store (SQLite persistence)
- Memory Layer (Knowledge entities)
- Bulk task monitoring (multi-UPID)
- Progress percentage extraction from log lines
- Any changes to existing PVE client methods or models
- Any new PVE API endpoints

---

## 17. Domain Function Signatures (Design Only — No Code)

```python
async def task_wait(
    client: PveClient,
    upid: str,
    *,
    node: str | None = None,
    timeout: int = 120,
    poll_interval: float = 1.0,
) -> dict[str, object]:
    """Poll task_status until stopped or timeout. Returns final status."""

async def task_follow(
    client: PveClient,
    upid: str,
    node: str,
    *,
    timeout: int = 120,
    poll_interval: float = 1.0,
) -> dict[str, object]:
    """Poll task_status + task_log, accumulate lines, return status + log."""
```

### MCP Tool Definitions (Design Only — No Code)

```python
# task_wait_tool
name = "task_wait"
tier = ToolTier.READ
input_schema = {
    "type": "object",
    "properties": {
        "upid": {"type": "string", "description": "UPID of the task to wait for"},
        "node": {"type": "string", "description": "Node hint (recommended for cross-cluster UPIDs)"},
        "timeout": {"type": "integer", "description": "Maximum seconds to wait", "default": 120},
        "poll_interval": {"type": "number", "description": "Seconds between status checks", "default": 1.0},
    },
    "required": ["upid"],
}

# task_follow_tool
name = "task_follow"
tier = ToolTier.READ
input_schema = {
    "type": "object",
    "properties": {
        "upid": {"type": "string", "description": "UPID of the task to follow"},
        "node": {"type": "string", "description": "Node where the task runs (required for log access)"},
        "timeout": {"type": "integer", "description": "Maximum seconds to wait", "default": 120},
        "poll_interval": {"type": "number", "description": "Seconds between poll cycles", "default": 1.0},
    },
    "required": ["upid", "node"],
}
```

---

## 18. Summary

| Tool | Reads status | Reads log | Node required | Default poll | Default timeout | Log in response |
|------|-------------|-----------|---------------|--------------|-----------------|-----------------|
| `task_wait` | ✅ every cycle | ❌ | No | 1.0s | 120s | ❌ |
| `task_follow` | ✅ every cycle | ✅ every cycle | **Yes** | 1.0s | 120s | ✅ (full) |

Both tools:
- Are READ-tier (no POST, no mutation)
- Use existing PVE client methods (no new endpoints)
- Respect ADR-0009 limits
- Follow PVE 9.x primary, PVE 8.x secondary compatibility
- Return gracefully on timeout (not an error)
- Support exponential backoff on transient errors
- Return `task_not_found` on 404/501 for missing tasks
- Are isolated in `domains/tasks/service.py` for future Operator integration
