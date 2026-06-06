# Domain Read Tools — Implementation Report

**Date:** 2026-06-04  
**Context:** Implementation of `cluster_info` and `node_status` READ tools, completing the first useful Proxmox data path.

---

## Tools Implemented

### 1. `cluster_info`

**MCP Tool** → calls **Cluster Domain** → calls **PVE Client** → `GET /api2/json/cluster/status` → Proxmox API → MCP Response

| Layer | File | Responsibility |
|-------|------|----------------|
| MCP Tool Registration | `src/mcp_proxmox/mcp/registry/tools.py` | `cluster_info_tool` handler, `ToolDefinition(name="cluster_info", tier=ToolTier.READ)` |
| Domain Service | `src/mcp_proxmox/domains/cluster/service.py` | Filters cluster entry from node entries, computes online/offline counts |
| PVE Client | `src/mcp_proxmox/pve/client/core.py` (existing) | `get_cluster_status()` → `list[ClusterStatusEntry]` |
| Response Model | `src/mcp_proxmox/pve/models/responses.py` (existing) | `ClusterStatusEntry` (type, name, version, quorate, online, ...) |

**Input schema:** `{}` (no arguments)

**Output:**
```json
{
  "name": "pve",
  "version": 1,
  "quorate": 1,
  "nodes": {
    "total": 3,
    "online": 2,
    "offline": 1,
    "members": [
      {"type": "node", "name": "pve1", "online": 1, ...},
      {"type": "node", "name": "pve2", "online": 0, ...}
    ]
  }
}
```

### 2. `node_status`

**MCP Tool** → calls **Node Domain** → calls **PVE Client** → `GET /api2/json/nodes/{node}/status` → Proxmox API → MCP Response

| Layer | File | Responsibility |
|-------|------|----------------|
| MCP Tool Registration | `src/mcp_proxmox/mcp/registry/tools.py` | `node_status_tool` handler, `ToolDefinition(name="node_status", tier=ToolTier.READ)` |
| Domain Service | `src/mcp_proxmox/domains/nodes/service.py` | Delegates to `client.get_node(node_name)`, returns `NodeStatus.model_dump()` |
| PVE Client | `src/mcp_proxmox/pve/client/core.py` (existing) | `get_node(node_name)` → `NodeStatus` |
| Response Model | `src/mcp_proxmox/pve/models/responses.py` (existing) | `NodeStatus` (cpu, loadavg, memory, rootfs, swap, uptime, kversion, pveversion, cpuinfo) |

**Input schema:**
```json
{
  "type": "object",
  "properties": {
    "node_name": {"type": "string", "description": "Name of the node (e.g. pve1)"}
  },
  "required": ["node_name"]
}
```

**Output:**
```json
{
  "cpu": 0.25,
  "uptime": 12345,
  "pveversion": "8.2.4",
  "kversion": "6.8.12-2-pve",
  "loadavg": [0.1, 0.2, 0.3],
  "memory": {"total": 17179869184, "used": 8589934592, "free": 8589934592},
  "rootfs": {"total": 107374182400, "used": 53687091200, "avail": 53687091200},
  "swap": {"total": 4294967296, "used": 0, "free": 4294967296},
  "cpuinfo": {"model": "AMD EPYC 7452", "cpus": 8}
}
```

---

## Complete Call Path

```
Client (MCP Host)
   │
   ├── JSON-RPC: tools/call { name: "cluster_info" }
   │
   ▼
StdioTransport.serve_forever()          # src/mcp_proxmox/mcp/transport/stdio.py
   │
   ▼
MinimalMcpServer.handle_message()       # src/mcp_proxmox/mcp/handlers/server.py
   │
   ├── _dispatch("tools/call", params)
   │   │
   │   ▼
   ├── _handle_tool_call(params)
   │   │
   │   ├── registry.get_tool("cluster_info")
   │   │
   │   ├── policy.authorize(READ)        # src/mcp_proxmox/policy/engine.py
   │   │
   │   ▼
   ├── await tool.handler(arguments)
   │   │
   │   ▼
   ├── cluster_info_tool(params)         # src/mcp_proxmox/mcp/registry/tools.py
   │   │
   │   ▼
   ├── await cluster_info(client)        # src/mcp_proxmox/domains/cluster/service.py
   │   │
   │   ▼
   ├── await client.get_cluster_status() # src/mcp_proxmox/pve/client/core.py
   │   │
   │   ├── GET /api2/json/cluster/status
   │   │   → httpx.AsyncClient.get(url, headers=Authorization)
   │   │   → PVE API → JSON response → validated via ClusterStatusEntry model
   │   │
   │   ▼
   │   ← list[ClusterStatusEntry]
   │
   │   Filter: cluster entry + node entries
   │   Compute: online/offline counts
   │
   ▼
← {"content": [{"type": "text", "text": "{...}"}]}
```

---

## Files Changed/Created

| File | Action | Lines | Purpose |
|------|--------|-------|---------|
| `src/mcp_proxmox/domains/cluster/service.py` | **created** | 41 | `cluster_info` domain service |
| `src/mcp_proxmox/domains/cluster/__init__.py` | **modified** | 4 | Export `cluster_info` |
| `src/mcp_proxmox/domains/nodes/service.py` | **modified** | 15 → 22 | Added `node_status` domain service |
| `src/mcp_proxmox/domains/nodes/__init__.py` | **modified** | 3 → 4 | Export `node_status` |
| `src/mcp_proxmox/mcp/registry/tools.py` | **modified** | 93 → 149 | Registered `cluster_info` + `node_status`, refactored handler naming |
| `tests/unit/test_domain_cluster.py` | **created** | 59 | Unit tests for `cluster_info` domain service |
| `tests/unit/test_domain_nodes.py` | **created** | 48 | Unit tests for `node_status` domain service |
| `tests/unit/test_mcp_server.py` | **modified** | 201 → 316 | Added MCP-level tests, extended fake client, updated tool count |

---

## Test Results

```
33 passed in 1.47s
0 lint errors
```

| Test file | Tests | What it verifies |
|-----------|-------|-----------------|
| `test_domain_cluster.py` | 3 | `cluster_info` extracts cluster entry, computes online/offline, handles edge cases |
| `test_domain_nodes.py` | 2 | `node_status` returns full NodeStatus dict, passes correct node_name |
| `test_mcp_server.py` (MinimalMcpServerTests) | +3 | `cluster_info` MCP call returns cluster data, `node_status` returns node details, `node_status` requires node_name |
| `test_mcp_server.py` (McpProcessTests) | updated | `tools/list` returns 4 tools, `server_info` lists all 4 |

---

## Available Tools (current)

| Tool | Arguments | READ tier | Domain | PVE Endpoint |
|------|-----------|-----------|--------|-------------|
| `server_info` | none | ✓ | — | — |
| `list_nodes` | none | ✓ | nodes | `GET /nodes` |
| `cluster_info` | none | ✓ | cluster | `GET /cluster/status` |
| `node_status` | `node_name` (required) | ✓ | nodes | `GET /nodes/{node}/status` |

Next logical tools in Phase 1A: `vm_list`, `container_list`, cluster/VM/container status detail tools.
