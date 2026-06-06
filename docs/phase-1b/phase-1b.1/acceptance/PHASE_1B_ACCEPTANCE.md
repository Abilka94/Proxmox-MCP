# Phase 1B.1 — Acceptance

**Date:** 2026-06-06
**Status:** ACCEPTED

---

## Goal

Implement and validate the Task Domain read layer — three MCP tools (`task_list`, `task_status`, `task_log`) providing read-only task history and status visibility into a Proxmox VE cluster. All tools are READ-tier, covered by unit tests, and confirmed working on a real 3-node PVE 8.x cluster.

---

## Scope (Phase 1B.1)

| Component | Status |
|-----------|--------|
| Pydantic models (`TaskListEntry`, `TaskStatus`, `TaskLogEntry`) | Implemented |
| PVE client methods (`get_tasks`, `get_task_status`, `get_task_log`) | Implemented |
| Domain service (`task_list`, `task_status`, `task_log`) | Implemented |
| MCP tools v1 (`task_list`, `task_status`, `task_log`) | Implemented |
| MCP tools v2 (`task_wait`, `task_follow`) | Deferred to Phase 1B.2 |
| Task cancel (`POST .../stop`) | Deferred to Phase 1C |

---

## Implemented MCP Tools (3)

| Tool | Tier | Parameters | PVE Endpoint |
|------|------|-----------|-------------|
| `task_list` | READ | `node` (opt), `user` (opt), `vmid` (opt), `type` (opt), `status` (opt), `limit` (opt, default 50, max 500) | `GET /cluster/tasks` (client-side filtering) + `GET /nodes/{node}/tasks` (when node specified) |
| `task_status` | READ | `upid` (req), `node` (opt) | `GET /cluster/tasks/{upid}/status` → fallback `GET /nodes/{node}/tasks/{upid}/status` |
| `task_log` | READ | `upid` (req), `node` (req), `start` (opt) | `GET /nodes/{node}/tasks/{upid}/log` |

---

## Live Connection Validation

**Script:** `scripts/test_live_connection.py`

```
> python scripts/test_live_connection.py --config config/local.yaml
config loaded: connection=local
connected: 3 node(s)
  - pve3 (online)
  - pve2 (online)
  - pve (online)
```

Config loading, PveClient construction, HTTPS authentication, and PVE API response parsing confirmed on a 3-node Proxmox VE 8.x cluster.

---

## Live Task Validation

**Script:** `scripts/validate_live_task.py`

| Result | Count |
|--------|-------|
| Passed | 15 |
| Failed | 0 |
| Skipped | 0 |

All 15 test cases passed across all 3 tools and edge cases.

---

## Validation Remediation

Over two remediation cycles, 5 defects were found and fixed:

| Defect | Cause | Fix | File |
|--------|-------|-----|------|
| `limit` param → 400 | PVE 8.x rejects `limit` on `/cluster/tasks` | Apply limit client-side via `entries[:limit]` | `pve/client/core.py` |
| Filter params → 400 | PVE 8.x rejects `status`, `source`, `user`, `vmid`, `type` | Apply all filtering client-side; use node-level endpoint when `node` specified | `pve/client/core.py` |
| `task_status` cluster → 501 | PVE 8.x has no cluster-level status endpoint | Expand fallback from 400-only to 400+501; node-level endpoint works | `pve/client/core.py` |
| `httpx.URL(upid).path` strips `UPID:` prefix | `httpx.URL` interprets `UPID:` as URL scheme | Replace with `urllib.parse.quote(upid, safe='')` | `pve/client/core.py` |
| `task_log` → 400 | Same UPID encoding issue (Bug #4) | Resolved by Bug #4 fix | `pve/client/core.py` |

---

## PVE 8.x Compatibility Findings

During live validation, the following endpoint behaviours were observed:

| Endpoint | Behaviour | Notes |
|----------|-----------|-------|
| `GET /cluster/tasks` | 200 OK (no filter params accepted) | Filters applied client-side |
| `GET /nodes/{node}/tasks` | 200 OK (only `limit` param accepted) | Node-level endpoint used when `node` specified |
| `GET /cluster/tasks/{upid}/status` | **501 Not Implemented** | Endpoint does not exist on this PVE 8.x version |
| `GET /nodes/{node}/tasks/{upid}/status` | 200 OK | Node-level status endpoint fully functional |
| `GET /nodes/{node}/tasks/{upid}/log` | 200 OK | Log endpoint fully functional |

This contradicts the design document assumption that cluster-level status works on PVE 8.x. The node-level fallback handles this correctly.

---

## Test Coverage

| Layer | Tests | Scope |
|-------|-------|-------|
| PVE client (tasks) | 9 | Task list with client-side limit/filters, status with fallback, log with start param |
| Domain (tasks) | 7 | task_list, task_status, task_log — filter passthrough, field mapping |
| MCP integration (tasks) | 6 | Registration, routing, missing params, named responses |
| Full suite | 114 | All passing |

---

## Known Limitations

1. **`task_status` requires `node` on PVE 8.x** — cluster-level endpoint returns 501. If no `node` is provided and cluster-level status returns 501, the error propagates. The node-level fallback works when `node` is given.
2. **Client-side filtering** — all filter parameters (`status`, `user`, `vmid`, `type`) are applied client-side. PVE's API returns all tasks and filtering happens in-memory. Keep `limit` small to avoid large fetches.
3. **No `task_wait` / `task_follow`** — polling-based wait and log-follow are deferred to Phase 1B.2.
4. **No `task_cancel`** — deferred to Phase 1C.
5. **No persistence** — tasks are not stored locally. History is available only through the PVE API.
6. **No progress parsing** — log lines may contain progress percentages, but no structured progress extraction is implemented.

## Required Token Permissions

| Endpoint | Minimum Privilege |
|----------|------------------|
| `GET /cluster/tasks` | `Sys.Audit` on `/` |
| `GET /cluster/tasks/{upid}/status` | `Sys.Audit` on `/` |
| `GET /nodes/{node}/tasks/{upid}/status` | `Sys.Audit` on `/` |
| `GET /nodes/{node}/tasks/{upid}/log` | `Sys.Audit` on `/` |

**Recommended role:** `PVEAuditor` (built-in Proxmox VE role). Same token used in Phase 1A is sufficient.

---

## Open Questions for Next Phase

1. Should `task_status` make `node` a **required** parameter given that cluster-level endpoint returns 501 on PVE 8.x?
2. For `task_wait` (Phase 1B.2), what default timeout and poll interval are appropriate? Current proposal: timeout=300s, poll_interval=1.0s.
3. Should `task_log` support a `tail` parameter (return last N lines) in addition to `start`?
4. Should the design document be updated to reflect that `GET /cluster/tasks/{upid}/status` is not available on all PVE 8.x versions?

---

## Phase 1B.1 Status: ACCEPTED

The Task Domain read layer is fully implemented, unit-tested (114 tests), live-validated on a 3-node Proxmox VE 8.x cluster, and all code-level defects discovered during validation have been remediated.
