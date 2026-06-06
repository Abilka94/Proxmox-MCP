# Live Cluster Configuration Guide

**Date:** 2026-06-06
**Purpose:** Prepare `config/local.yaml` and run first live test against a real Proxmox VE cluster.

---

## 1. Config File Location

```
D:\AI-Stack\Proxmox\Proxmox-MCP\config\local.yaml
```

This file is listed in `.gitignore` — secrets will **not** be committed.

---

## 2. Configuration Format

The format must match the Pydantic models in `src/mcp_proxmox/config/models.py`. All models use `extra="forbid"` — unknown keys cause validation errors.

### Full Structure

```yaml
connection:
  id: "<connection-name>"
  host: "<pve-api-url>"
  token_id: "<token-id>"
  token_secret: "<token-secret>"
  verify_ssl: <true|false>

policy:
  mode: READ_ONLY          # only valid value
  memory:
    allow_write: <true|false>

orchestrator:
  max_concurrent_per_node: <number>      # default: 5
  max_concurrent_cluster: <number>        # default: 15
  node_request_timeout_sec: <number>      # default: 30
  aggregate_threshold: <number>           # default: 500

cache:
  cluster_resources_ttl_sec: <number>    # default: 30
  node_status_ttl_sec: <number>          # default: 15

logging:
  level: <DEBUG|INFO|WARNING|ERROR>      # default: INFO
  format: <json|console>                 # default: console

audit:
  path: "<audit-log-path>"               # default: data/audit.log

subsystems:
  logs:
    enabled: <true|false>                # default: true
    max_lines: <number>                  # default: 500
```

### Obligatory Parameters (`connection` section)

| Field | Type | Validation | Description |
|-------|------|-----------|-------------|
| `connection.id` | string | min_length=1 | Arbitrary connection label (e.g. `"production"`) |
| `connection.host` | URL | valid HttpUrl | PVE API base URL (e.g. `https://pve1.example.com:8006`) |
| `connection.token_id` | string | min_length=1 | API token ID (e.g. `root@pam!mcp-token`) |
| `connection.token_secret` | string | min_length=1 | API token secret |
| `connection.verify_ssl` | bool | — | SSL verification (set `false` for self-signed certs) |

### Obligatory Parameters (`policy` section)

| Field | Type | Description |
|-------|------|-------------|
| `policy.mode` | enum: `READ_ONLY` | Only valid value in current implementation |
| `policy.memory.allow_write` | bool | Allow the memory system to persist learned data |

### Optional Parameters (all have defaults)

| Section | Default Values |
|---------|---------------|
| `orchestrator` | `max_concurrent_per_node: 5`, `max_concurrent_cluster: 15`, `node_request_timeout_sec: 30`, `aggregate_threshold: 500` |
| `cache` | `cluster_resources_ttl_sec: 30`, `node_status_ttl_sec: 15` |
| `logging` | `level: INFO`, `format: console` |
| `audit` | `path: data/audit.log` |
| `subsystems` | `logs.enabled: true`, `logs.max_lines: 500` |

---

## 3. Values in local.yaml vs Environment Variables

The current implementation supports **two approaches**:

| Approach | Mechanism | Use Case |
|----------|-----------|----------|
| **Hardcoded in local.yaml** | Values written directly | Simplest for validation sprint. No env vars needed. |
| **Env var placeholders** | `${VAR_NAME}` in YAML values, expanded from `os.environ` | Production: secrets never written to disk. |

### Recommended: Hardcoded for Validation Sprint

Since `config/local.yaml` is in `.gitignore`, it is safe to write secrets directly:

```yaml
connection:
  id: "validation"
  host: "https://192.168.1.100:8006"
  token_id: "root@pam!mcp-validator"
  token_secret: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  verify_ssl: false
```

### Alternative: Env Var Placeholders (for later production use)

```yaml
connection:
  id: "production"
  host: "${PVE_HOST}"
  token_id: "${PVE_TOKEN_ID}"
  token_secret: "${PVE_TOKEN_SECRET}"
  verify_ssl: true
```

With `.env`:
```
PVE_HOST=https://pve.production.example:8006
PVE_TOKEN_ID=root@pam!prod-token
PVE_TOKEN_SECRET=prod-secret-value
```

---

## 4. Minimal Configuration for Live Cluster

### Minimal `config/local.yaml`

```yaml
connection:
  id: "live-test"
  host: "https://192.168.1.100:8006"
  token_id: "root@pam!mcp-live-test"
  token_secret: "pve-api-token-secret-value"
  verify_ssl: false

policy:
  mode: READ_ONLY
  memory:
    allow_write: true

logging:
  level: DEBUG
  format: console
```

This is the minimum required. All other sections (`orchestrator`, `cache`, `audit`, `subsystems`) use their defaults and can be omitted.

**Important:** Replace the placeholder values with your actual cluster data:
- `192.168.1.100:8006` → your PVE host IP and port
- `root@pam!mcp-live-test` → your API token ID (created via Datacenter → Permissions → API Tokens)
- `pve-api-token-secret-value` → the token secret shown once at token creation

---

## 5. Commands

All commands run from `D:\AI-Stack\Proxmox\Proxmox-MCP` with the virtual environment activated.

### 5.1 Validate Configuration

```powershell
# Method 1: explicit --config argument
python scripts/validate_config.py --config config/local.yaml

# Method 2: MCP_PROXMOX_CONFIG env var
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"
python scripts/validate_config.py

# Expected output on success:
#   config valid: connection=live-test
#
# On failure (e.g. missing field, invalid URL):
#   config invalid: ...
#   Exit code: 1
```

### 5.2 Start MCP Server (stdio mode)

```powershell
# One-liner with env var inline
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"; mcp-proxmox

# Or set env var permanently for the session
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"
mcp-proxmox
```

The server starts in stdio mode and waits for MCP JSON-RPC messages on stdin. It will output log lines to stderr.

### 5.3 Quick Connection Test (server_info)

The server_info tool does **not** call the PVE API — it returns only static server metadata. To verify the server starts and responds:

```powershell
# Send a minimal MCP initialize request via stdin
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}' | mcp-proxmox
```

Expected response on stdout (formatted):
```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}}}}
```

### 5.4 Connection Test with PVE API Call

To verify the PVE API connection works, use one of these approaches:

**Option A — MCP Inspector (requires Node.js):**
```powershell
# Install and run the MCP Inspector
npx @modelcontextprotocol/inspector mcp-proxmox
```

Set the environment variable `MCP_PROXMOX_CONFIG=config/local.yaml` in the Inspector UI, then call the `list_nodes` or `cluster_info` tool.

**Option B — Python one-liner (no external tools):**

Create `scripts/test_live_connection.py`:

```python
"""Quick live connection test — does NOT modify the cluster."""
from mcp_proxmox.config import load_config
from mcp_proxmox.pve.auth import auth_config_from_app_config
from mcp_proxmox.pve.client import PveClient
import asyncio

async def main():
    config = load_config()
    client = PveClient(auth_config_from_app_config(config))
    nodes = await client.get_nodes()
    print(f"Connected: {len(nodes)} node(s) found")
    for n in nodes:
        print(f"  • {n.node} ({n.status})")

asyncio.run(main())
```

Run:
```powershell
$env:MCP_PROXMOX_CONFIG = "config/local.yaml"
python scripts/test_live_connection.py
```

Expected output:
```
Connected: 2 node(s) found
  • pve1 (online)
  • pve2 (online)
```

### 5.5 Run Existing Test Suite

```powershell
# Ensure all unit tests still pass before/after live test
python -m pytest tests/unit/ -v
```

---

## 6. Troubleshooting

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `Config file not found: config/local.yaml` | File doesn't exist or wrong CWD | Create file or set `$env:MCP_PROXMOX_CONFIG` to absolute path |
| `Invalid YAML mapping at line N` | Indentation error in YAML | Use 2-space indentation, ensure colons are correct |
| `Missing required environment variable: PVE_HOST` | Using `${VAR}` placeholders without setting env vars | Either set the env var or hardcode the value in local.yaml |
| `PVE API transport error` | Wrong host URL or network unreachable | Verify `connection.host` is reachable: `curl https://your-host:8006/api2/json/` |
| `PVE API request failed (401 ...)` | Invalid token_id or token_secret | Regenerate token in PVE Web UI → Datacenter → Permissions → API Tokens |
| `PVE API request failed (403 ...)` | Token lacks permissions | Ensure token has at least read-level permissions (e.g. built-in `PVEAuditor` role) |
| `PVE API request failed (501 ...)` | SSL certificate verification failed | Set `verify_ssl: false` for self-signed certificates |

---

## 7. Security Checklist

- [ ] `config/local.yaml` is listed in `.gitignore` — verify with `git status`
- [ ] Never copy `config/local.yaml` as `config/default.yaml` (default.yaml is tracked)
- [ ] API token has minimum required permissions (read-only for validation sprint)
- [ ] For production, use env var placeholders + secure env injection (systemd, Docker, Kubernetes)
- [ ] Token secret appears once at creation — store in a password manager if needed again
