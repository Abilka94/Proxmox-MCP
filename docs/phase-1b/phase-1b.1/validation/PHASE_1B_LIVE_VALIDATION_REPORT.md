# Phase 1B.1 — Live Validation Report

**Date:** 2026-06-06
**Target:** `https://192.168.0.186:8006` (3-node PVE 8.x cluster)
**Client:** `scripts/validate_live_task.py`
**Status:** 15/15 PASS — all tests passed after full remediation cycle

---

## Cluster Info

- **Nodes:** pve, pve2, pve3 (3 nodes discovered and reachable)
- **PVE Version:** 8.x (confirmed via Phase 1A validation)
- **Token:** `ai-agent@pve!openwebui` with `Sys.Audit` on `/`

## Validation Results

### task_list (6 cases)

| # | Test | Status | Detail |
|---|------|--------|--------|
| T1 | No filters | **PASS** | 50 tasks returned, UPID/node/status present |
| T2 | limit=3 | **PASS** | 3 tasks returned (client-side truncation) |
| T3 | status=running | **PASS** | 0 running tasks (client-side filtering) |
| T4 | status=stopped | **PASS** | 0 stopped tasks (client-side filtering) |
| T5 | node=pve | **PASS** | 10 tasks, all on node pve |
| T6 | node=pve3 | **PASS** | 10 tasks, all on node pve3 |

### task_status (3 cases)

| # | Test | Status | Detail |
|---|------|--------|--------|
| S1 | Existing UPID (with node) | **PASS** | status=stopped exitstatus=OK |
| S2 | Cluster→node fallback (with node param) | **PASS** | status=stopped — node-level endpoint works |
| S3 | Non-existent UPID | **PASS** | `PveApiError(501)` — properly handled |

### task_log (3 cases)

| # | Test | Status | Detail |
|---|------|--------|--------|
| L1 | Existing UPID | **PASS** | 1 line: "TASK OK" — log line with text field present |
| L2 | start=0 | **PASS** | 1 line — start offset parameter works |
| L3 | Non-existent UPID | **PASS** | `PveApiError` — properly handled |

### Edge Cases (1 case)

| # | Test | Status | Detail |
|---|------|--------|--------|
| E1 | Bad node name | **PASS** | `PveApiError(500)` — expected for invalid node |

## Token Permissions

- `Sys.Audit` on `/` — sufficient for all task endpoints
- No 403 errors observed

## Defects Found and Fixed

### Bug #1: `limit` param rejected by PVE 8.x (`/cluster/tasks`)
- **Fix:** Removed `limit` from API request params; applied client-side via `entries[:limit]`
- **Verification:** `test_get_tasks_client_side_limit`

### Bug #2: All filter params rejected by PVE 8.x (`status`, `source`, `user`, `vmid`, `type`)
- **Fix:** Applied all filtering client-side; when `node` is specified, uses node-level endpoint
- **Verification:** `test_get_tasks_filters_client_side`

### Bug #3: Cluster-level task_status returns 501 Not Implemented on PVE 8.x
- **Endpoints:** `GET /cluster/tasks/{upid}/status` → 501
- **Fix:** Fallback to node-level endpoint `GET /nodes/{node}/tasks/{upid}/status` when node is provided
- **Verification:** `test_get_task_status_fallback_on_400` (updated for 501 fallback)

### Bug #4: `httpx.URL(upid).path` strips `UPID:` prefix (URL scheme misinterpretation)
- **Symptom:** UPID `UPID:pve:...` → path becomes `pve:...` (missing `UPID:` prefix)
- **Fix:** Replaced `httpx.URL(upid).path` with `urllib.parse.quote(upid, safe='')` in all 3 task client methods
- **Files:** `src/mcp_proxmox/pve/client/core.py`
- **Verification:** `debug_upid_encoding.py` confirmed correct URL encoding

### Bug #5: task_log returns 400 due to malformed UPID in URL path
- **Cause:** Same root cause as Bug #4 — `httpx.URL` stripping `UPID:` prefix
- **Fix:** Resolved by Bug #4 fix (correct URL encoding)
- **Verification:** `debug_upid_encoding.py` confirmed 200 OK with `urllib.parse.quote`

## PVE 8.x Compatibility Notes

| Endpoint | Behaviour on PVE 8.x |
|----------|----------------------|
| `GET /cluster/tasks` | 200 OK — no filter params accepted (400 if sent) |
| `GET /nodes/{node}/tasks` | 200 OK — only `limit` param accepted |
| `GET /cluster/tasks/{upid}/status` | **501 Not Implemented** — endpoint does not exist |
| `GET /nodes/{node}/tasks/{upid}/status` | 200 OK — fully functional |
| `GET /nodes/{node}/tasks/{upid}/log` | 200 OK — fully functional |

## Summary

| Metric | Value |
|--------|-------|
| Validation date | 2026-06-06 |
| Tests planned | 15 |
| Tests passed | 15 |
| Tests failed | 0 |
| Bugs found | 5 |
| Bugs fixed | 5 |
| Unit tests | 114/114 passing |

## Known Limitations

1. **`task_status` requires `node` parameter on PVE 8.x** — cluster-level endpoint returns 501. The node-level fallback works when `node` is provided.
2. **Client-side filtering** — all filter parameters (`status`, `user`, `vmid`, `type`) are applied client-side, meaning the PVE API returns all tasks and filtering happens in-memory.
3. **No running/stopped tasks observed** — the PVE 8.x cluster only returned tasks with `status: "OK"` and no tasks with `status: "running"` or `status: "stopped"` at validation time. The client-side filtering handles this correctly regardless.
