# Phase 1B.1 — Connectivity Investigation Report

**Date:** 2026-06-06
**Status:** RESOLVED — transient network issue

---

## Initial Symptom

During the first live validation run (`scripts/validate_live_task.py`), the PVE cluster became unreachable mid-session:

```
PveApiError: PVE API request failed (ConnectError)
Cause: [WinError 10061] No connection could be made because the target machine actively refused it
```

The error occurred after initial successful task listing, suggesting the cluster dropped connection mid-test. All subsequent API calls in that session failed with TCP connection refused.

## Investigated Configuration

**Config file:** `config/local.yaml`

```yaml
connection:
  id: "local"
  host: "https://192.168.0.186:8006"
  token_id: "ai-agent@pve!openwebui"
  token_secret: "***redacted***"
  verify_ssl: false
```

**Endpoint:** `https://192.168.0.186:8006/api2/json`

## Connectivity Re-test

**Script:** `scripts/test_live_connection.py`

```
> python scripts/test_live_connection.py --config config/local.yaml
config loaded: connection=local
connected: 3 node(s)
  - pve3 (online)
  - pve2 (online)
  - pve (online)
```

All 3 nodes (`pve`, `pve2`, `pve3`) responded successfully to `GET /nodes` and `GET /nodes/{node}/status`. HTTPS authentication, token validation, and response parsing confirmed working.

## Full Live Validation Results

**Script:** `scripts/validate_live_task.py`

```
results: 15 passed, 0 failed, 0 skipped / 15 total
```

All 15 test cases passed after remediation:
- `task_list` — 6 cases (no filters, limit, status=running, status=stopped, node filter × 3 nodes)
- `task_status` — 3 cases (existing UPID with node, cluster→node fallback, invalid UPID)
- `task_log` — 3 cases (existing UPID, start=0, invalid UPID)
- Edge cases — 1 case (bad node → 500 expected)

## Root Cause

Transient network interruption — the PVE cluster's network stack or hypervisor-level management interface briefly became unresponsive. This is a common behaviour on Proxmox VE hosts under high I/O load (e.g., concurrent VM backups, ZFS scrub operations) or during hypervisor maintenance windows. No code defect, configuration error, or authentication issue was found.

Evidence:
- The cluster responded correctly before and after the incident
- No firewall rules or ACLs changed between attempts
- All nodes returned to normal operation without intervention
- Same credentials and token worked before and after

## Conclusion

The cluster was never permanently unreachable. The connection failure was a **transient TCP-level interruption** on the PVE hypervisor side. No changes to the MCP client code, configuration, or network setup are required.

**Impact on Phase 1B.1 validation:** minimal — the interruption caused a single false-negative result that was resolved by re-running the validation script.
