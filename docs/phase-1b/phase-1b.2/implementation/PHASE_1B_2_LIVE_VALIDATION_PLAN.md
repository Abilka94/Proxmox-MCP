# Phase 1B.2 — Live Validation Plan

**Date:** 2026-06-06
**Target:** Real PVE 9.x cluster (primary), PVE 8.x cluster (secondary, best effort)

---

## 1. Purpose

Validate `task_wait` and `task_follow` against a real PVE cluster to confirm:
- Polling loop behaviour matches the design
- Timeout and `timed_out: true` work correctly
- Log accumulation and `log_truncated: true` work correctly
- PVE 8.x cluster-level fallback (or lack thereof) behaves as documented
- Error handling for non-existent UPIDs works correctly

## 2. Pre-requisites

- Configured `opencode.json` pointing to a live PVE cluster
- PVE cluster running (preferably PVE 9.x; PVE 8.x for secondary)
- At least one node in the cluster
- Network connectivity from the test host to the PVE API

## 3. Validation Scenarios

### 3.1 `task_wait` — Already Completed Task

1. Call `task_list` with `status=running` to find a completed task's UPID, or use any known UPID
2. Call `task_wait` with that UPID and `timeout=30`
3. **Expected:** Immediate return with `completed: true`, `status: "stopped"`, `exitstatus`, `wait_seconds` near 0

### 3.2 `task_wait` — Poll Until Completion

Use a long-running task (e.g., a replication job, backup, or apt update):
1. Trigger a task (via CLI or wait for an existing running task)
2. Call `task_wait` with that UPID and `timeout=120`
3. **Expected:** Returns after the task finishes with `completed: true`, `status: "stopped"`, `wait_seconds` > 0

### 3.3 `task_wait` — Timeout

Use a long-running task (e.g., a backup job, replication, or `apt update`):
1. Trigger a task that runs for more than a few seconds
2. Call `task_wait` with its UPID, `timeout=2`
3. **Expected:** Returns in ~2 seconds with `completed: false`, `timed_out: true`, `status: "running"`, `wait_seconds` ≈ 2.0

### 3.4 `task_wait` — Non-Existent UPID

1. Call `task_wait` with a completely fake UPID like `UPID:pve:00000000:FFFFFFFF:00000000:fake:root@pam:`
2. **Expected:** Returns `error: "task_not_found"`

### 3.5 `task_wait` — Without Node (PVE 8.x only)

On PVE 8.x:
1. Use a valid UPID but omit the `node` parameter
2. **Expected:** Returns `error: "task_not_found"` (because cluster-level status returns 501)
3. Then call with the correct `node` — **expected:** succeeds with `completed: true`

On PVE 9.x:
1. **Expected:** Works even without `node` (cluster-level endpoint is functional)

### 3.6 `task_follow` — Already Completed Task with Log

1. Use any known completed task's UPID and its node
2. Call `task_follow` with `timeout=30`
3. **Expected:** Returns `completed: true`, `status: "stopped"`, `lines` array with log entries, `total_lines` > 0

### 3.7 `task_follow` — Poll Until Completion with Log

1. Trigger a task that produces log output (e.g., `apt update`)
2. Call `task_follow` with that UPID and `timeout=120`, `poll_interval=1.0`
3. **Expected:** Returns `completed: true`, `lines` contains accumulated log from start to finish, `total_lines` reflects all lines

### 3.8 `task_follow` — Timeout with Partial Log

1. Call `task_follow` with a running task's UPID and `timeout=2`, `poll_interval=1.0`
2. **Expected:** Returns in ~2 seconds with `completed: false`, `timed_out: true`, `lines` contains at least some log lines, `total_lines` > 0

### 3.9 `task_follow` — Without Node

1. Call `task_follow` with a valid UPID but omit `node`
2. **Expected:** Returns `error` (field-level validation)

### 3.10 `task_follow` — Non-Existent UPID

1. Call `task_follow` with a fake UPID and any node name
2. **Expected:** Returns `error: "task_not_found"`

## 4. Data Validation Checks

For all successful `task_follow` calls:
- `lines` entries must have `"text"` key (string, non-empty for real tasks)
- `lines` entries may have `"lineno"` key (integer, if PVE provides it)
- `total_lines` must equal `len(lines)`
- `wait_seconds` must be a positive float
- `status` must be `"stopped"` for completed tasks
- `exitstatus` must be present for completed tasks (usually `"OK"`)

## 5. Acceptance Criteria

All scenarios in Section 3 must produce the expected result. A scenario "passes" if:
- The response shape matches the design document (correct keys, types)
- Timeouts are respected (±1s tolerance)
- Error responses contain the expected `error` field
- No unexpected exceptions are raised
- The tool does not hang longer than `timeout + 5s`

## 6. Non-Targets (Out of Scope)

- Performance benchmarking under load
- Concurrent polling session limits (semaphore tested in unit tests)
- `task_cancel` / `task_stop` (Phase 1C)
- POST operations
- Operator Mode
- Job Store persistence

## 7. Reporting

Results should be recorded in:
`docs/phase-1b/phase-1b.2/implementation/PHASE_1B_2_LIVE_VALIDATION_REPORT.md`

Template:
```markdown
# Phase 1B.2 — Live Validation Report

**Date:** YYYY-MM-DD
**Cluster:** PVE X.Y (node count: N)
**Tester:** [name]

## Results

| # | Scenario | Status | Notes |
|---|----------|--------|-------|
| 1 | task_wait — already completed | PASS/FAIL | |
| 2 | task_wait — poll until completion | PASS/FAIL | |
| ... | ... | ... | |

## Issues Found

- [ ] Issue 1: ...
- [ ] Issue 2: ...

## Summary

- Total scenarios: N
- Passed: N
- Failed: N
- Blocked: N
```
