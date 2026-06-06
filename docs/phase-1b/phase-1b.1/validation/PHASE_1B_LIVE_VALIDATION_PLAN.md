# Phase 1B.1 — Live Validation Plan

**Date:** 2026-06-06
**Target cluster:** `https://192.168.0.186:8006` (3-node PVE 8.x, from `config/local.yaml`)
**Token role:** `PVEAuditor` (Sys.Audit on `/`)

---

## 1. Validation Script: `scripts/validate_live_task.py`

New standalone script (parallel to `validate_live_mcp.py`) that validates only the 3 new task tools against the real cluster.

### 1.1 Task List — `task_list`

| # | Test Case | Parameters | Expected |
|---|-----------|------------|----------|
| T1 | No filters | `{}` | `{count, tasks}` with tasks array, count ≥ 0 |
| T2 | With limit | `{limit: 5}` | `count ≤ 5` |
| T3 | Status filter: running | `{status: "running"}` | All returned tasks have `status: "running"` |
| T4 | Status filter: stopped | `{status: "stopped"}` | All returned tasks have `status: "stopped"` |
| T5 | Node filter | `{node: "<node>"}` | Tasks filtered to that node |

### 1.2 Task Status — `task_status`

| # | Test Case | Parameters | Expected |
|---|-----------|------------|----------|
| S1 | From task_list entry | `{upid: <from T1>}` | `{upid, status, exitstatus}` |
| S2 | Cluster→node fallback | `{upid: <cross-node>, node: <name>}` | Status returned (cluster fails → node fallback) |
| S3 | Non-existent UPID | `{upid: "UPID:fake:...invalid..."}` | PVE 400 error, propagated as error in result |

### 1.3 Task Log — `task_log`

| # | Test Case | Parameters | Expected |
|---|-----------|------------|----------|
| L1 | Full log | `{upid: <stopped>, node: <name>}` | `{upid, lines, total_lines}` |
| L2 | With start offset | `{upid: <stopped>, node: <name>, start: 0}` | Same as L1 |
| L3 | Non-existent UPID | `{upid: "UPID:fake:...", node: <name>}` | PVE 400 error |

### 1.4 Edge Cases

| # | Test Case | Parameters | Expected |
|---|-----------|------------|----------|
| E1 | Empty cluster (no recent tasks) | `task_list(limit=1)` | `count=0`, `tasks=[]` |
| E2 | Running task | Pick UPID with `status=running` from T3 | `status="running"`, `exitstatus=null` |
| E3 | Stopped task | Pick UPID with `status=stopped` from T4 | `status="stopped"`, `exitstatus="OK"` or error |

---

## 2. Endpoints Tested

| Endpoint | Test Cases |
|---|---|
| `GET /cluster/tasks?limit=N&source=&user=&status=` | T1–T5 |
| `GET /cluster/tasks/{upid}/status` | S1, S3 |
| `GET /nodes/{node}/tasks/{upid}/status` | S2 (fallback) |
| `GET /nodes/{node}/tasks/{upid}/log?start=N` | L1–L3 |

## 3. Token Permissions Checked

- `Sys.Audit` on `/` — required for all task endpoints
- If any endpoint returns 403, document as known limitation (same as `node_updates`)

## 4. Success Criteria

- All tests in T1–T5, S1–S3, L1–L3 pass (PASS or SKIP) with no FAIL
- Empty/error cases handled gracefully (no unhandled exceptions)
- UPID returned verbatim, never modified
- Task `t` → `text` mapping verified

## 5. Script Location

`scripts/validate_live_task.py` — will be created before execution.
