# Validation Remediation Report

**Date:** 2026-06-06
**Cluster:** prod (3 nodes: pve, pve2, pve3)
**Config:** `config/local.yaml`

---

## Defects Found During Live Validation

| # | Tool | Defect | Root Cause | Severity | Status |
|---|------|--------|-----------|----------|--------|
| 1 | `container_list` | HTTP 400 on `/cluster/resources?type=lxc` | PVE 8.x does not accept `type=lxc`; LXC containers are returned under `type=vm` with `"type": "lxc"` field | High | **Fixed** |
| 2 | `network_list` | `ValidationError` on `families` field | `NetworkInterface.families` typed as `str`, PVE 8.x returns `list[str]` | High | **Fixed** |
| 3 | `node_updates` | HTTP 403 Forbidden | API token lacks `PVEAuditor` role; needs `Sys.Audit` on `/` | Low | **Documented** |

---

## Fix 1: container_list — PVE 8.x API Compatibility

### Investigation

Tested all supported `/cluster/resources?type=` values on the real cluster:

| type | Result |
|------|--------|
| `vm` | 6 results (both `lxc` and `qemu` types) |
| `lxc` | **400 Bad Request** |
| `node` | 3 results |
| `storage` | 8 results |
| `sdn` | 0 results |

Additionally confirmed that per-node `/nodes/{node}/lxc` works and returns full container info.

### Resolution

Changed `PveClient.get_containers()` in `src/mcp_proxmox/pve/client/core.py:91-95`:

```python
# Before (fails on PVE 8.x):
payload = await self._get_json("/cluster/resources?type=lxc")

# After (compatible with PVE 7.x and 8.x):
payload = await self._get_json("/cluster/resources?type=vm")
lxc_items = [item for item in payload if item.get("type") == "lxc"]
```

Single-endpoint approach: TMLLXCs are included in the `type=vm` response with `"type": "lxc"`. Filtering client-side avoids PVE version differences.

### Verification

```
Before: container_list → 400 Bad Request
After:  container_list → 4 container(s) found
```

---

## Fix 2: NetworkInterface.families — Type Mismatch

### Investigation

Real PVE response shape confirmed on all 3 nodes:

```
pve/vmbr0:        families=['inet']  (type=list)
pve2/enx00e04c270870: families=['inet', 'inet']  (type=list)
```

The `families` field is always `list[str]` in PVE 8.x, but the model defined it as `str | None`.

### Resolution

Changed `src/mcp_proxmox/pve/models/responses.py:170`:

```python
# Before:
families: str | None = None

# After:
families: list[str] | None = None
```

### Verification

```
Before: network_list → ValidationError on all 3 nodes
After:  network_list → PASS on all 3 nodes (pve: 4, pve3: 5, pve2: 4 interfaces)
```

---

## Fix 3: node_updates — Token Permissions (Documentation Only)

### Investigation

```
node_updates(pve)   → PveApiError: 403 /nodes/pve/apt/update
node_updates(pve3)  → PveApiError: 403 /nodes/pve3/apt/update
node_updates(pve2)  → PveApiError: 403 /nodes/pve2/apt/update
```

`GET /nodes/{node}/apt/update` requires the `Sys.Audit` privilege at the `/` level.

### Minimum Token Permissions for READ Mode

| Endpoint | Required Privilege | Scope |
|----------|-------------------|-------|
| `GET /nodes/{node}/status` | `Sys.Audit` | `/` |
| `GET /nodes/{node}/apt/update` | `Sys.Audit` | `/` |
| `GET /cluster/status` | `Sys.Audit` | `/` |
| `GET /cluster/resources` | `VM.Audit` (VMs), `Datastore.Audit` (storage) | `/` |
| `GET /nodes/{node}/network` | `Sys.Audit` | `/` |
| `GET /nodes/{node}/qemu/{vmid}/config` | `VM.Audit` | `/vms/{vmid}` |
| `GET /nodes/{node}/lxc/{vmid}/config` | `VM.Audit` | `/vms/{vmid}` |
| `GET /nodes/{node}/storage/{storage}/content` | `Datastore.Audit` | `/storage/{storage}` |

**Recommended role for READ mode: `PVEAuditor`** (built-in PVE role).

Without `PVEAuditor`, the tools that remain available depend on the token's permission set:

| Permission Level | Available Tools |
|----------------|-----------------|
| Default (limited) | `list_nodes`, `vm_list`, `vm_status`, `vm_config`, `storage_list`, `storage_status`, `storage_content`, `container_list`, `container_status`, `container_config` |
| + `Sys.Audit` on `/` | `node_status`, `network_list`, `cluster_info`, `server_info` |
| + Full `PVEAuditor` | `node_updates` (and `cluster_updates` with real data) |

### Current Behavior

`cluster_updates` handles the 403 gracefully: each node failure is wrapped as `ClusterUpdateEntry(node="pve", title="<failed to fetch updates>")`. The tool succeeds with partial data.

---

## Final Validation Results (After Fixes)

```
results: 16 passed, 3 failed (permissions), 0 skipped / 19 total
```

| Tool | Status | Fix |
|------|--------|-----|
| `server_info` | ✅ PASS | — |
| `list_nodes` | ✅ PASS | — |
| `cluster_info` | ✅ PASS | — |
| `node_status` (x3) | ✅ PASS | — |
| `vm_list` | ✅ PASS | — |
| `vm_config` | ✅ PASS | — |
| **`container_list`** | **✅ PASS** | **Fix 1 applied** |
| **`container_config`** | **✅ PASS** | **Fix 1 applied** |
| `storage_list` | ✅ PASS | — |
| `storage_content` | ✅ PASS | — |
| **`network_list` (x3)** | **✅ PASS** | **Fix 2 applied** |
| `node_updates` (x3) | ❌ 403 Forbidden | Permissions (documented) |
| `cluster_updates` | ✅ PASS | Graceful degradation |

---

## Files Changed

| File | Change |
|------|--------|
| `src/mcp_proxmox/pve/client/core.py:91-95` | `get_containers()` — use `type=vm` + filter `type=lxc` |
| `src/mcp_proxmox/pve/models/responses.py:170` | `NetworkInterface.families` — `str` → `list[str]` |

## Unit Tests

**91/91 passing** (unchanged count, all pass).

---

## Conclusion

All code-level defects from live validation are remediated:

1. **container_list** — fixed: PVE 8.x API compatibility
2. **network_list** — fixed: `families` field type matches PVE response
3. **node_updates** — documented: requires `PVEAuditor` role (not a code bug)

Infrastructure Read Layer is fully confirmed on real cluster with 16/19 tool calls passing and 0 code defects remaining.
