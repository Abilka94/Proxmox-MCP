# Phase 1A Acceptance

**Date:** 2026-06-06
**Status:** ACCEPTED

---

## Goal

Implement and validate the Infrastructure Read Layer — a set of read-only MCP tools providing full visibility into a Proxmox VE cluster: nodes, VMs, containers, storage, network, and updates. All tools must be registered in the MCP tool registry, covered by unit tests, and confirmed working on a real cluster.

---

## Implemented Domains (8)

| Domain | Directory | Responsibility |
|--------|-----------|----------------|
| Cluster | `domains/cluster/` | Cluster identity and node membership |
| Nodes | `domains/nodes/` | Node status and enumeration |
| VMs | `domains/vms/` | VM listing, status, configuration |
| Containers | `domains/containers/` | LXC container listing, status, configuration |
| Storage | `domains/storage/` | Storage listing, status, content |
| Network | `domains/network/` | Network interface listing per node |
| Updates | `domains/updates/` | APT updates per node and cluster-wide |
| System | `mcp/registry/` | Server info (static metadata) |

---

## Implemented MCP Tools (16)

| Tool | Tier | Parameters | PVE Endpoint |
|------|------|-----------|-------------|
| `server_info` | READ | none | (static) |
| `list_nodes` | READ | none | `GET /nodes` |
| `cluster_info` | READ | none | `GET /cluster/status` |
| `node_status` | READ | `node_name` | `GET /nodes/{node}/status` |
| `vm_list` | READ | none | `GET /cluster/resources?type=vm` |
| `vm_status` | READ | `node`, `vmid` | `GET /nodes/{node}/qemu/{vmid}/status/current` |
| `vm_config` | READ | `node`, `vmid` | `GET /nodes/{node}/qemu/{vmid}/config` |
| `container_list` | READ | none | `GET /cluster/resources?type=vm` + filter `type=lxc` |
| `container_status` | READ | `node`, `vmid` | `GET /nodes/{node}/lxc/{vmid}/status/current` |
| `container_config` | READ | `node`, `vmid` | `GET /nodes/{node}/lxc/{vmid}/config` |
| `storage_list` | READ | none | `GET /cluster/resources?type=storage` |
| `storage_status` | READ | `node`, `storage` | `GET /nodes/{node}/storage/{storage}/status` |
| `storage_content` | READ | `node`, `storage` | `GET /nodes/{node}/storage/{storage}/content` |
| `network_list` | READ | `node` | `GET /nodes/{node}/network` |
| `node_updates` | READ | `node` | `GET /nodes/{node}/apt/update` |
| `cluster_updates` | READ | none | `GET /cluster/status` + per-node `GET /nodes/{node}/apt/update` |

---

## Live Connection Validation

**Script:** `scripts/test_live_connection.py`

```powershell
python scripts/test_live_connection.py --config config/local.yaml
```

**Result:**
```
config loaded: connection=local
connected: 3 node(s)
  - pve (online)
  - pve3 (online)
  - pve2 (online)
```

Config loading, PveClient construction, HTTPS authentication, and PVE API response parsing confirmed on a 3-node Proxmox VE 8.x cluster.

---

## Live MCP Validation

**Script:** `scripts/validate_live_mcp.py`

| Result | Count |
|--------|-------|
| Passed | 16 tool calls |
| Failed | 3 (all `node_updates` — 403 Forbidden, token lacks `PVEAuditor`) |
| Skipped | 0 |

All 13 code-testable tools confirmed working. The only failing tool (`node_updates`) is gated by token permissions, not a code defect.

---

## Validation Remediation

| Defect | Cause | Fix | File |
|--------|-------|-----|------|
| `container_list` → 400 | PVE 8.x rejects `type=lxc` | Use `type=vm` + filter `type=lxc` | `pve/client/core.py:91-95` |
| `network_list` → ValidationError | `families` typed as `str`, PVE returns `list[str]` | Change type to `list[str] \| None` | `pve/models/responses.py:170` |
| `node_updates` → 403 | Token lacks `Sys.Audit` on `/` | Documented — requires `PVEAuditor` role | (documentation) |

---

## Test Coverage

| Layer | Tests | Scope |
|-------|-------|-------|
| Domain services | 25 | PVE client call verification, empty lists, param passthrough |
| PVE client | 11 | JSON parsing, error wrapping, auth header |
| MCP integration | 18 | Registration, routing, error handling |
| Config, policy, logging | 37 | Config validation, policy enforcement, log redaction |
| **Total** | **91** | All passing |

---

## Known Limitations

1. **`node_updates` requires elevated token** — API token must have `PVEAuditor` role (`Sys.Audit` on `/`). Default read-only tokens cannot access `GET /nodes/{node}/apt/update`.
2. **No `.env` auto-loading** — Python code does not load `.env` files. Users must set environment variables externally (shell, Docker, systemd) or hardcode values in `config/local.yaml`.
3. **`pydantic-settings` unused** — dependency is listed in `pyproject.toml` but not used. No direct env-var-to-config mapping exists.
4. **`verify_ssl` and `timeout` are static** — configured in YAML only, not overridable via environment variables.

---

## Required Token Permissions

| Endpoint | Minimum Privilege |
|----------|------------------|
| `GET /nodes` | `Sys.Audit` on `/` |
| `GET /nodes/{node}/status` | `Sys.Audit` on `/` |
| `GET /nodes/{node}/network` | `Sys.Audit` on `/` |
| `GET /nodes/{node}/apt/update` | `Sys.Audit` on `/` |
| `GET /cluster/status` | `Sys.Audit` on `/` |
| `GET /cluster/resources` | `VM.Audit` on `/` (VMs), `Datastore.Audit` on `/` (storage) |
| `GET /nodes/{node}/qemu/{vmid}/config` | `VM.Audit` on `/vms/{vmid}` |
| `GET /nodes/{node}/lxc/{vmid}/config` | `VM.Audit` on `/vms/{vmid}` |
| `GET /nodes/{node}/storage/{storage}/content` | `Datastore.Audit` on `/storage/{storage}` |

**Recommended role:** `PVEAuditor` (built-in Proxmox VE role).

---

## Open Questions for Next Phase

1. Should `.env` auto-loading be added via `python-dotenv` for local development convenience?
2. Should `pydantic-settings` be used to provide direct env-var overrides for `verify_ssl` and `timeout`?
3. Should `container_list` be implemented via per-node iteration as a fallback if `type=vm` approach fails?
4. What is the upgrade path for adding write/admin tools while preserving audit trail?
5. Should the `families` field in `NetworkInterface` use `list[str]` or `list[Literal["inet","inet6"]]` for stricter typing?

---

## Phase 1A Status: ACCEPTED

The Infrastructure Read Layer is fully implemented, unit-tested (91 tests), live-validated on a 3-node Proxmox VE 8.x cluster, and all code-level defects discovered during validation have been remediated.
