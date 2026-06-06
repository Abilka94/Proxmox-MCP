# Live Validation Execution Plan

**Date:** 2026-06-06
**Status:** Plan (no code written)

---

## 1. Fact Check: `scripts/test_live_connection.py`

| Check | Result |
|-------|--------|
| File existed? | **No** — never present in the repository |
| Was it implemented? | **No** — no commits, no branches, no stubs |
| Was it deleted? | **No** — cannot delete what never existed |
| Is the mention in `LIVE_CLUSTER_CONFIGURATION_GUIDE.md` an error? | **Yes** — the guide references a non-existent file under "Option B — Python one-liner (no external tools)". This is a documentation error in the guide. The section instructed the user to *create* the file, implying it does not yet exist, which contradicts the "one-liner" heading. Correct approach: remove the file-creation suggestion and use an inline command instead. |

---

## 2. Existing Validation Tooling

### Scripts present in `scripts/`:

| Script | Purpose | Tests PVE Connectivity? |
|--------|---------|------------------------|
| `scripts/validate_config.py` | Validates YAML format + Pydantic model validation | **No** — only config syntax, no HTTP calls |
| `scripts/generate_tool_catalog.py` | Generates tool documentation | **No** |

### Entry point (`mcp-proxmox`):

Starts the full MCP stdio server, which instantiates `PveClient` and makes real HTTP calls to PVE. This is the **only** existing code path that exercises real PVE connectivity.

### Unit tests (`tests/unit/`):

Use `respx` (HTTP mock) and `FakePveClient` — no real network calls.

---

## 3. Correct Live Validation Procedure

### Phase 1: Validate Config Format (no network)

```powershell
python scripts/validate_config.py --config config/local.yaml
```

Exit code 0 = config is syntactically valid and passes Pydantic validation.

### Phase 2: Start MCP Server (no explicit test script needed)

The MCP server itself is the validation tool. After config validation:

```powershell
# Start the server (listens on stdin/stdout for MCP JSON-RPC)
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"
mcp-proxmox
```

### Phase 3: Test PVE Connectivity (read-only, safe)

With the server running, send JSON-RPC messages via stdin. The following sequence exercises the PVE API in ascending order of complexity:

| Step | Tool | PVE Endpoint | What It Verifies |
|------|------|-------------|------------------|
| 1 | `server_info` | (none — static) | Server starts, MCP protocol works |
| 2 | `list_nodes` | `GET /nodes` | Authentication, basic network, JSON parsing |
| 3 | `cluster_info` | `GET /cluster/status` + per-node aggregation | Multi-endpoint orchestration |
| 4 | `vm_list` | `GET /cluster/resources?type=vm` | Resource endpoint |
| 5 | `storage_list` | `GET /cluster/resources?type=storage` | Storage endpoint |

All are `ToolTier.READ` — guaranteed read-only by the Policy Engine.

### Phase 4: Manual stdin Test (quick smoke test)

Without an MCP client, send raw JSON-RPC to the server:

```powershell
# First: test server_info (no PVE call)
@'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"server_info","arguments":{}}}
'@ | mcp-proxmox
```

If both return valid JSON-RPC responses, the server runs and responds.

### Phase 5: Full PVE Connectivity Test (inline one-liner, no file needed)

Use Python directly to instantiate the PVE client and call `GET /nodes`:

```powershell
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"
python -c "
import asyncio
from mcp_proxmox.config import load_config
from mcp_proxmox.pve.auth import auth_config_from_app_config
from mcp_proxmox.pve.client import PveClient
async def t():
    c = load_config()
    client = PveClient(auth_config_from_app_config(c))
    nodes = await client.get_nodes()
    print(f'Connected: {len(nodes)} node(s)')
    for n in nodes:
        print(f'  - {n.node} ({n.status})')
asyncio.run(t())
"
```

This performs a real `GET /api2/json/nodes` against the cluster. It is **read-only**, uses the existing `PveClient` and `load_config()` without any new code, and confirms end-to-end: config parse → auth header → HTTPS → JSON response → Pydantic validation.

---

## 4. Recommended Validation Workflow Summary

```
1. Create config/local.yaml           (fill with your cluster data)
2. python scripts/validate_config.py --config config/local.yaml    (config OK?)
3. python -c "..."                    (PVE connectivity OK?)
4. mcp-proxmox                        (start MCP server for real use)
```

---

## 5. Result: `test_live_connection.py` Created and Executed

### File created

`scripts/test_live_connection.py` — validates config loading, PveClient creation, node list retrieval, with typed error output. Uses only existing `load_config()`, `auth_config_from_app_config()`, `PveClient`.

### Execution result (2026-06-06)

```powershell
python scripts/test_live_connection.py --config config/local.yaml
```

```
config loaded: connection=local
connected: 3 node(s)
  - pve (online)
  - pve3 (online)
  - pve2 (online)
```

Config loaded, PVE API authenticated, 3 nodes discovered — full connectivity confirmed.

### Example run

```powershell
# With explicit config path:
python scripts/test_live_connection.py --config config/local.yaml

# Or via MCP_PROXMOX_CONFIG env var:
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"
python scripts/test_live_connection.py
```

### Error examples

```
# Config file not found:
ConfigError: Config file not found: config/missing.yaml

# Invalid credentials:
PveApiError (401): PVE API request failed (/nodes)

# Unreachable host:
PveApiError (None): PVE API transport error (/nodes)
