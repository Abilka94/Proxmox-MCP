# Phase 1B.1 — Validation Remediation Report

**Date:** 2026-06-06
**Status:** 2 bugs found, both fixed

---

## Bug #1: PVE 8.x rejects `limit` query param on `/cluster/tasks`

### Symptom
```
GET /api2/json/cluster/tasks?limit=50
→ 400: "limit is not defined in schema and the schema does not allow additional properties"
```

### Root Cause
PVE 8.x `/cluster/tasks` endpoint enforces strict schema validation and does **not** accept a `limit` parameter as a query string. The parameter is rejected before reaching the handler logic.

### Impact
All `task_list` calls failed with 400 because `get_tasks()` unconditionally sent `limit=50` (the default) as a query parameter.

### Fix (client/core.py:185-217)
- Removed `limit` from the PVE API request params
- `limit` is now enforced **client-side** by slicing the returned list: `entries[:limit]`
- PVE API receives no `limit` param and returns its default number of tasks
- The client truncates to the requested limit before returning

### Files Changed
`src/mcp_proxmox/pve/client/core.py` — `get_tasks()` method

### Tests Updated
- `test_get_tasks_passes_limit_and_filters` → replaced with `test_get_tasks_with_node_uses_node_endpoint_and_limit` (tests that `limit` goes to node endpoint only) and `test_get_tasks_client_side_limit` (tests client-side truncation)
- `test_get_tasks_filters_client_side` — new test verifying client-side filtering

---

## Bug #2: PVE 8.x rejects ALL filter query params on task endpoints

### Symptom
```
GET /api2/json/cluster/tasks?status=running
→ 400: "status is not defined in schema and the schema does not allow additional properties"

GET /api2/json/nodes/pve/tasks?status=running
→ 400 (same error)

GET /api2/json/cluster/tasks?source=pve
→ 400 (same error)
```

### Root Cause
PVE 8.x task endpoints (`/cluster/tasks` and `/nodes/{node}/tasks`) accept **no** filter query parameters (`status`, `source`, `user`, `type`, `vmid`). Only `limit` is accepted (and only at the node-level endpoint).

This affects our specific PVE 8.x cluster version. Other PVE installations may behave differently.

### Impact
All `task_list` calls with any filter parameter (`status`, `node`, `user`, `vmid`, `type`) would fail with 400.

### Fix (client/core.py:185-217)
All filtering is now performed **client-side**:
1. Fetch all tasks from the chosen endpoint (cluster or node-level)
2. Apply filters (`status`, `user`, `vmid`, `type_filter`) as list comprehensions
3. Apply `limit` by slicing
4. Return the filtered, truncated list

Additionally, when a `node` filter is provided, the client now uses the **node-level** endpoint `/nodes/{node}/tasks?limit=N` instead of `/cluster/tasks`, which is more efficient (returns only that node's tasks).

### Files Changed
`src/mcp_proxmox/pve/client/core.py` — `get_tasks()` method

### Tests Updated
- `test_get_tasks_with_node_uses_node_endpoint_and_limit` — verifies node-level endpoint usage
- `test_get_tasks_filters_client_side` — creates mock data with mixed statuses and verifies client-side filtering
- `test_get_tasks_client_side_limit` — verifies client-side truncation

---

## Verification

All 114 unit tests pass (was 112 before, 2 new client-side tests added):

```
tests/unit/test_pve_client.py::test_get_tasks_with_node_uses_node_endpoint_and_limit  PASSED
tests/unit/test_pve_client.py::test_get_tasks_filters_client_side  PASSED
tests/unit/test_pve_client.py::test_get_tasks_client_side_limit  PASSED
```

## Notes

- Both bugs are caused by PVE 8.x strict parameter validation, not by the Proxmox API specification
- The fixes are backward-compatible: they work whether PVE accepts server-side filters or not
- Client-side filtering may return fewer results than the `limit` value if filters are very restrictive
- The `limit` parameter default (50) and maximum (500) are still enforced client-side
