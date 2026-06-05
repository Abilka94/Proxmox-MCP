# Competitive Analysis: MCP-Proxmox AI Infrastructure Operator

**Date:** 2026-06-05
**Scope:** Proxmox VE MCP ecosystem competitive landscape
**Context:** MCP-Proxmox (ours) vs JerichoJack/Proxmox-MCP vs bsahane/mcp-proxmox vs RekklesNA/ProxmoxMCP-Plus

---

## Table of Contents

1. [Overview of Analysed Projects](#1-overview-of-analysed-projects)
2. [Project-by-Project Analysis](#2-project-by-project-analysis)
   - 2.1. [ProxmoxMCP-Plus (RekklesNA)](#21-proxmoxmcp-plus-rekklesna)
   - 2.2. [bsahane/mcp-proxmox](#22-bsahanemcp-proxmox)
   - 2.3. [JerichoJack/Proxmox-MCP](#23-jerichojackproxmox-mcp)
3. [Comparative Analysis](#3-comparative-analysis)
4. [Useful Ideas To Borrow](#4-useful-ideas-to-borrow)
5. [Ideas To Reject](#5-ideas-to-reject)
6. [Feature Gap Analysis](#6-feature-gap-analysis)
7. [Recommendations](#7-recommendations)

---

## 1. Overview of Analysed Projects

| Project | Language | Stars | Tools | Maturity | Architecture |
|---|---|---|---|---|---|
| **MCP-Proxmox (ours)** | Python 3.12+ | — | 12 (read-only) | Phase 1A | Layered (Transport → Handlers → Policy → Domain → Client) |
| **ProxmoxMCP-Plus** | Python 3.11+ | ~236 | ~30+ | v0.5.7, 22 releases | MCP + OpenAPI dual surface, monolith |
| **bsahane/mcp-proxmox** | Python 3.10+ | — | ~65 (many stubs) | Experimental | Monolithic, multi-cluster registry |
| **JerichoJack/Proxmox-MCP** | Python 3.x | <5 | 13 | Alpha | Event-driven (input listeners → core → MCP) |

---

## 2. Project-by-Project Analysis

### 2.1. ProxmoxMCP-Plus (RekklesNA)

**Repository:** https://github.com/RekklesNA/ProxmoxMCP-Plus
**PyPI:** `proxmox-mcp-plus` (v0.5.7)
**License:** MIT

#### Architectural Model

Dual-surface architecture: MCP (stdio + Streamable HTTP) and OpenAPI bridge running simultaneously. Core Proxmox operations are proxied through a `proxmoxer`-based client layer. Long-running Proxmox tasks are wrapped in a persistent `JobStore` (SQLite-backed) that provides `job_id` alongside raw `task_id` (UPID). Tool execution is guarded by a `command_policy` and optional `approval_token`. The OpenAPI bridge is protected by bearer auth (`PROXMOX_API_KEY`). Configuration is via a single `config.json` file.

```
MCP Client (stdio/HTTP) ─┐
                          ├── Tool Layer ── ProxmoxClient (proxmoxer) ── PVE API
OpenAPI Client (HTTP) ────┘        │
                                   ├── JobStore (SQLite)
                                   ├── CommandPolicy
                                   └── Security (tokens, approval, CORS)
```

#### Strengths

- **Persistent job tracking** — SQLite-backed `JobStore` with `list_jobs`, `get_job`, `poll_job`, `cancel_job`, `retry_job`. Survives restarts.
- **Dual MCP + OpenAPI surface** — same operational logic exposed via both protocols without duplication.
- **Production-grade Docker** — multi-profile `docker-compose.yml` with GHCR images, Streamable HTTP support at `/mcp`.
- **SSH-backed container commands** — `execute_container_command` with `command_policy` guardrails and `authorized_keys` management.
- **Full mutation lifecycle** — VM/LXC create/start/stop/delete, snapshot/rollback/delete, backup/restore, ISO download/delete.
- **Security controls** — DNS rebinding protection, Host/Origin allowlists, `approval_token` for high-risk ops, TLS validation by default.
- **Real testing** — `pytest` with coverage, `ruff`, `mypy`, `pip-audit`, live Proxmox e2e entry points (`run_real_e2e.py`).
- **Active maintenance** — 22 releases in 6 weeks, responsive to issues.

#### Weaknesses

- **proxmoxer dependency** — synchronous library wrapped in async context; blocks event loop under load. No native `httpx.AsyncClient`.
- **No tool tiers** — all tools available to any connected client. No READ_ONLY/OPERATOR/ADMIN distinction.
- **No policy engine** — guard is per-tool `command_policy` for specific operations, not a cross-cutting tiered authorization layer.
- **No EntityRef/knowledge model** — no structured resource addressing, no memory layer, no dependency tracking.
- **No event-driven architecture** — purely request-response; cannot react to Proxmox events.
- **No PBS (Proxmox Backup Server) integration** — backup/restore uses `vzdump` only.
- **No correlation IDs** — no request-scoped logging context, making audit trail reconstruction harder.
- **No structured error types** — errors propagate as generic exceptions, not typed domain errors.
- **Config is monolithic** — single `config.json` with no schema validation (JSON Schema or Pydantic).
- **No built-in rate limiting** — relies on client-side or reverse proxy controls.

#### Target Use Case

Teams needing production-ready MCP-native Proxmox automation with HTTP/OpenAPI integration for non-MCP tooling. Focus on day-2 operations (VM/LXC lifecycle, backup, snapshots) with persistent async job tracking.

---

### 2.2. bsahane/mcp-proxmox

**Repository:** https://github.com/bsahane/mcp-proxmox
**PyPI:** N/A (no published package)
**License:** Not specified

#### Architectural Model

Monolithic Python package (`src/proxmox_mcp/`) with ~18 modules. Uses `FastMCP` from the official MCP Python SDK. PVE communication via synchronous `proxmoxer` library wrapped in `async def` tools. Supports multi-cluster mode via `ClusterRegistry` with pattern-based routing. Includes specialised modules for CloudInit (NoCloud ISO generation), RHCOS/OpenShift, Windows VM configuration, Docker Swarm orchestration, security (MFA, Vault, certificates), advanced networking (VLAN, VPN, firewall), monitoring stacks (Prometheus/Grafana/ELK), AI/ML predictive scaling (simulated), and IaC (Terraform/Ansible/GitOps).

```
server.py (FastMCP) ── client.py (proxmoxer, synchronous)
    │
    ├── cloudinit.py        — NoCloud ISO generator
    ├── rhcos.py            — RHCOS/Ignition configurator
    ├── windows.py          — Windows VM configurator (UEFI, TPM, virtio)
    ├── docker_swarm.py     — Docker Swarm orchestration via QGA
    ├── security.py         — MFA, Vault, certificates
    ├── network.py          — VLAN, VPN (WireGuard/OpenVPN), firewall
    ├── monitoring.py       — Prometheus/Grafana/ELK stack (simulated)
    ├── storage_advanced.py — Replication, snapshot policies
    ├── ai_optimization.py  — ML predictive scaling (simulated)
    ├── infrastructure.py   — Terraform/Ansible/GitOps
    ├── cluster_manager.py  — Multi-cluster registry + routing
    └── server_multi_cluster.py — Aggregated multi-cluster tools
```

#### Strengths

- **Largest raw tool count** — ~65 tools spanning discovery, lifecycle, cloud-init, networking, security, monitoring, IaC.
- **Multi-cluster native** — built-in `ClusterRegistry` with pattern-based routing (`prod-:production`, `stg-:staging`), aggregation tools.
- **CloudInit expertise** — `cloudinit.py` generates real NoCloud ISOs with user/package/network/file injection.
- **Enterprise OS config** — Windows (UEFI/TPM/Secure Boot/virtio), RHCOS/OpenShift (Ignition ISO), Docker Swarm orchestration.
- **IaC integration** — Terraform plan/apply/destroy, Ansible playbook execution, GitOps sync exposed as MCP tools.
- **Security extras** — TOTP MFA, Let's Encrypt cert management, HashiCorp Vault, AES-256 key store.
- **Observability** — Prometheus/Grafana/Loki/ELK stack deployment via Docker Compose from MCP tools.
- **`confirm` + `dry_run` guard** — all destructive operations require explicit confirmation and support dry-run preview.
- **AI/ML extensions** — sklearn-based predictive scaling and anomaly detection (conceptually interesting though simulated).

#### Weaknesses

- **Sync/async mismatch** — `client.py` is fully synchronous (`requests` library), called from `async def` FastMCP tools. Blocks event loop under load.
- **Simulated/stub modules** — `ai_optimization.py`, `monitoring.py`, `network.py` use synthetic/mock data. ML models are simulated. Metrics collection is stubbed.
- **75+ dependencies** — `requirements.txt` includes sklearn, kubernetes, docker, elasticsearch, boto3, azure-storage-blob, google-cloud-storage — most unused in actual tool registration.
- **Hardcoded default password** — LXC creation falls back to `"changeMe123!"` when `PROXMOX_DEFAULT_LXC_PASSWORD` is unset.
- **No test coverage** — no `pytest` suite exists. `verify_mcp_tools.py` is a basic connectivity script.
- **Poor error handling** — bare `except:` and `except Exception as e:` throughout. No typed error hierarchy.
- **No version management** — no PyPI release, no CI/CD, no CHANGELOG. Single commit history indicates experimental quality.
- **No UPID polling (async)** — `wait_task` uses synchronous `time.sleep()` polling, not asyncio.
- **No structured logging** — no correlation IDs, no JSON formatter, no redaction.
- **No security tiers** — same as ProxmoxMCP-Plus — all tools accessible to any client.

#### Target Use Case

Experimental all-in-one Proxmox management with ambitious scope creep. Best suited as a feature reference/blueprint rather than production deployment. The CloudInit, Windows/RHCOS configurators, and IaC modules contain genuinely useful reference implementations.

---

### 2.3. JerichoJack/Proxmox-MCP

**Repository:** https://github.com/JerichoJack/Proxmox-MCP
**PyPI:** N/A
**License:** Not specified

#### Architectural Model

Event-driven architecture with three layers: Input (5 event listeners), Core (config, manager, Proxmox API pool), MCP (stdio + HTTP servers). Designed as a real-time notification hub rather than a comprehensive management console. Uses `proxmoxer` for API calls and the official `mcp` Python SDK. Supports STANDALONE/CLUSTERED/MIXED topology modes with auto-discovery. Also integrates with Proxmox Backup Server (PBS).

```
Input Listeners (WS/Email/Syslog/Gotify/Discord)
    ↓
core/manager.py (MCPManager)
    │
    ├── core/proxmox_api.py (ProxmoxAPIManager — connection pool for PVE + PBS)
    │
    ├── mcp_server.py (stdio, for local n8n)
    └── mcp_server_http.py (HTTP/WS, for remote clients)
```

#### Strengths

- **Event ingestion** — unique in the ecosystem. WebSocket event subscription, Email (IMAP), Syslog (UDP), Gotify, Discord polling.
- **Dual transport** — stdio for local agents + HTTP/WS for remote clients with feature parity.
- **PBS integration** — only project with explicit Proxmox Backup Server client support.
- **Notification output** — Discord webhook, Gotify, email, ntfy.sh as output channels.
- **n8n workflows** — includes complete n8n JSON exports for Discord ChatBot and AI agent integrations.
- **Topology awareness** — auto-discovery of cluster nodes via REST API with STANDALONE/CLUSTERED/MIXED modes.
- **Graceful shutdown** — proper signal handlers (SIGINT/SIGTERM) and asyncio cleanup.
- **Connection testing** — `--test-connection` CLI mode for pre-deployment validation.

#### Weaknesses

- **Shallow API coverage** — 13 tools, smallest set. No VM/LXC creation/deletion/migration, no snapshot, no backup execution, no firewall.
- **No UPID/task tracking** — VM/LXC commands are fire-and-forget. `get_node_tasks` lists history but no polling/cancel/retry.
- **No destructive guardrails** — `execute_vm_command("stop")` with `force=True` executes immediately. No `confirm` pattern.
- **No access control** — no tool tiers, no blacklist/whitelist. All connected clients get full tool access.
- **No input validation** — bare `Dict[str, Any]` handlers. No Pydantic/Zod schemas.
- **proxmoxer (sync)** — same sync-in-async problem as other proxmoxer-based projects.
- **Minimal testing** — basic HTTP health checks only. No unit tests, no integration tests.
- **No VM/LXC config read** — cannot fetch full VM/LXC configuration (only status). Missing `get_vm_config`, `get_lxc_config`.
- **No SSH/guest agent** — cannot execute commands inside VMs or containers.
- **Single-contributor** — 19 commits, 0 stars at time of analysis. Low community traction.

#### Target Use Case

Real-time Proxmox event monitoring and notification forwarding to AI agents. Better suited as an event ingestion layer than a management console.

---

## 3. Comparative Analysis

### 3.1. MCP Compatibility

| Aspect | Us (MCP-Proxmox) | ProxmoxMCP-Plus | bsahane/mcp-proxmox | JerichoJack/Proxmox-MCP |
|---|---|---|---|---|
| **MCP SDK** | Custom (minimal) | Custom | FastMCP (official) | Official `mcp` SDK |
| **Transport** | stdio only | stdio + Streamable HTTP | stdio only | stdio + HTTP/WS |
| **Tools/list** | Yes | Yes | Yes | Yes |
| **Tools/call** | Yes | Yes | Yes | Yes |
| **Resources** | Planned (T-209) | Yes (4 resources) | No | Yes (4 resources) |
| **Prompts** | No | No | No | Yes (5 prompts) |
| **Streaming** | No | No | No | No |
| **Pagination** | No | No | No | No |

**Verdict:** We lag in transport options (stdio-only vs stdio+HTTP) and resource exposure. ProxmoxMCP-Plus is the most complete MCP implementation.

### 3.2. PVE API Integration

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **HTTP library** | `httpx.AsyncClient` | `proxmoxer` (sync) | `proxmoxer` (sync) | `proxmoxer` (sync) |
| **Auth** | API Token | API Token | API Token | API Token |
| **SSL verify** | Configurable | Configurable | Configurable | Configurable |
| **PBS support** | No | No | No | Yes |
| **Response models** | Pydantic (strict) | Raw dicts | Raw dicts | Raw dicts |
| **Error wrapping** | `PveApiError` (typed) | Generic | Generic | Generic |

**Verdict:** Our `httpx.AsyncClient` with native async and typed `PveApiError` is architecturally superior to `proxmoxer`-based approaches. This is a genuine advantage.

### 3.3. Tool Registry

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **Registry pattern** | Explicit `ToolRegistry` class | Implicit (function list) | Implicit (decorators) | Implicit (official SDK) |
| **Tier metadata** | `ToolTier` (READ/OPERATOR/ADMIN) | None | None | None |
| **Policy binding** | `ToolPolicy` per tool | `command_policy` per op | `confirm` per tool | None |
| **Schema generation** | Manual JSON Schema | Manual | Auto (FastMCP) | Auto (official SDK) |
| **Discovery** | `tools/list` | `tools/list` | `tools/list` | `tools/list` |

**Verdict:** Our `ToolRegistry` with tier metadata and policy binding is unique and architecturally valuable. No competitor has equivalent abstraction.

### 3.4. Security

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **Policy engine** | `PolicyEngine` with `READ_ONLY` mode | None | None | None |
| **Tool tiers** | READ/OPERATOR/ADMIN | None | None | None |
| **Confirm guard** | Planned (Phase 5) | `confirm=true` | `confirm=true` | None |
| **Dry run** | Planned (Phase 5) | No | `dry_run=true` | No |
| **Approval token** | No | Yes (optional) | No | No |
| **Command policy** | Planned (Phase 5) | Yes | No | No |
| **API key (OpenAPI)** | N/A | Yes | N/A | No |
| **DNS/Host controls** | N/A | Yes | N/A | No |
| **Secret redaction** | Yes (in logging) | Claims but not verified | No | No |

**Verdict:** Our policy engine with tier-based authorization is a unique differentiator. ProxmoxMCP-Plus has better operational security (approval tokens, command policy). We should adopt `confirm=true` pattern.

### 3.5. Error Handling

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **Typed errors** | `PveApiError`, `PolicyDenied`, `McpProtocolError`, `ConfigError` | Generic | Generic | Generic |
| **Layer isolation** | Each layer has own error type | No | No | No |
| **Error responses** | JSON-RPC error codes | JSON-RPC error | JSON-RPC error | Text content |
| **Partial failure** | Planned (orchestrator) | No | No | Per-node try/except |
| **Parameter validation** | Inline `{"error": ...}` returns | No validation | `ValueError` on missing | No validation |

**Verdict:** Our typed error hierarchy is best-in-class among analysed projects. The inline parameter validation returning dicts instead of raising is a code quality issue we should fix.

### 3.6. Long Tasks / UPID

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **UPID parsing** | No | Yes | Yes | No |
| **Task polling** | Planned (T-203) | `poll_job` | `wait_task` (sync sleep) | No |
| **Persistent store** | No | SQLite `JobStore` | No | No |
| **Task retry** | No | `retry_job` | No | No |
| **Task cancel** | No | `cancel_job` | No | No |
| **Task list** | No | `list_jobs` | `list-tasks` (recent) | `get_node_tasks` |
| **Task log** | Planned | No | No | No |

**Verdict:** This is our biggest gap. ProxmoxMCP-Plus has the most complete long-task handling with persistent SQLite-backed job tracking including retry/cancel. We need to implement our Task domain (T-203) with at least equivalent capability.

### 3.7. VM/LXC Management

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **VM list** | Yes | Yes | Yes | Yes |
| **VM status** | Yes | Yes | Yes | Yes |
| **VM config** | Planned (T-207) | No | Yes | No |
| **VM create** | Planned (Phase 5) | Yes | Yes | No |
| **VM delete** | Planned (Phase 5) | Yes | Yes | No |
| **VM start/stop** | Planned (Phase 5) | Yes | Yes | Yes |
| **VM migrate** | Planned (Phase 5) | No | Yes | No |
| **VM resize disk** | No | No | Yes | No |
| **VM clone** | No | No | Yes | No |
| **VM configure** | No | No | Yes | No |
| **LXC create** | Planned (Phase 5) | Yes | Yes | No |
| **RRD metrics** | Planned (T-207) | No | Yes | No |

**Verdict:** bsahane has the most complete VM/LXC coverage. ProxmoxMCP-Plus covers the essentials (create/delete/start/stop). We have basic read-only coverage and need to close the gap with lifecycle management.

### 3.8. Storage

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **List** | Yes | Yes | Yes | Yes |
| **Status** | Yes | Yes | Yes | Yes |
| **Content** | Planned (T-201) | No | Yes | No |
| **Upload ISO** | Planned (Phase 5) | Yes | Yes | No |
| **Upload template** | No | No | Yes | No |
| **Replication** | No | No | Yes (simulated) | No |
| **Migration** | No | No | Yes (simulated) | No |
| **ZFS/LVM opt** | No | No | Yes (simulated) | No |

**Verdict:** Basic storage listing is covered. Content listing (T-201) should be prioritised. ISO management is useful but not urgent.

### 3.9. Network

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **List interfaces** | Yes (per-node) | No | Yes (bridges) | Yes |
| **NIC add/remove** | No | No | Yes | No |
| **Firewall rules** | Planned (T-202) | No | Yes | No |
| **SDN** | Planned (T-202) | No | No | No |
| **VLAN** | No | No | Yes | No |
| **VPN** | No | No | Yes (simulated) | No |

**Verdict:** Basic network listing is useful. SDN and firewall (T-202) are the right next steps. Advanced networking (VLAN/VPN) is out of scope.

### 3.10. Backup

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **List backups** | Planned (T-206) | Yes | Yes | Yes |
| **Create backup** | Planned | Yes | Yes | No |
| **Restore** | Planned | Yes | Yes | No |
| **Backup jobs** | Planned (T-206) | No | No | Yes (status only) |
| **PBS support** | No | No | No | Yes |

**Verdict:** ProxmoxMCP-Plus has the most complete backup story. T-206 (backup list + job status) is the minimum — full create/restore should follow.

### 3.11. Updates

| Aspect | Us | ProxmoxMCP-Plus | bsahane | JerichoJack |
|---|---|---|---|---|
| **List updates** | Yes | No | No | No |
| **APT update run** | No | No | No | No |
| **Repositories** | Planned | No | No | No |

**Verdict:** Our `node_updates` tool is unique. No competitor lists APT updates. This is a small but real differentiator.

---

## 4. Useful Ideas To Borrow

### 4.1. From ProxmoxMCP-Plus (High Priority)

| Idea | Why | How to Adapt |
|---|---|---|
| **Persistent job store** | SQLite-backed `JobStore` with `job_id` + `task_id` (UPID) is essential for Operator Mode. Survives restarts, supports retry/cancel | Implement as part of T-203. Use SQLite via `aiosqlite` for async. Store status, retry count, audit history |
| **`poll_job`, `retry_job`, `cancel_job`** | Complete job lifecycle management. `cancel_job` is critical for safety | Add to Task domain. Use PVE API `DELETE /nodes/{node}/tasks/{upid}` for cancel |
| **`confirm=true` guard pattern** | Simple, universal, prevents accidental mutations | Add to all mutation tools in Phase 5. Reject with clear message unless `confirm=True` |
| **Streamable HTTP transport** | Enables remote MCP clients. Docker-native | Add as secondary transport in Phase 2+. Keep stdio as primary |
| **Dual OpenAPI surface** | Exposes same logic to HTTP tooling without duplication | Not urgent. Consider when Operator Mode needs REST integration |
| **`command_policy` configuration** | YAML/JSON rules for allowed commands, patterns, blocked args | Useful for LXC guest command execution. Adapt to our policy engine |
| **Health/liveness endpoints** | `/livez`, `/readyz`, `/health` for Docker orchestration | Add as MCP server info tools, not separate HTTP endpoints |
| **Agent install deeplinks** | VS Code/Cursor one-click install buttons | Consider for README after MVP |

### 4.2. From bsahane/mcp-proxmox (Medium Priority)

| Idea | Why | How to Adapt |
|---|---|---|
| **Multi-cluster support** | `ClusterRegistry` with pattern-based routing (`prod-*`) | Consider in Phase 4+ (Diagnostic Traversal). Not urgent |
| **`dry_run=true` mode** | Returns what WOULD happen without executing | Add alongside `confirm=true` in Phase 5. Useful for "what if" queries |
| **CloudInit NoCloud ISO generation** | Enables "create VM with cloud-init" without external dependencies | Valuable for VM creation in Phase 5. Generate ISO via `genisoimage` or `mkisofs` |
| **Storage content listing** | List ISO templates, container templates on storage | Implement as T-201 priority. Needed before ISO download/create VM |
| **VM config reading** | `/nodes/{node}/qemu/{vmid}/config` — full VM configuration | Implement as T-207. Critical for diagnostic traversal |
| **LXC config reading** | `/nodes/{node}/lxc/{vmid}/config` — full container config | Implement as T-207 |
| **RRD metrics** | Historical CPU/memory/disk data via `/rrddata` | Implement as T-207. Useful for trend analysis in diagnostic mode |
| **Multi-cluster aggregation** | `list-all-vms-from-all-clusters`, `get-all-cluster-status` | Useful for large deployments. Consider after single-cluster is complete |
| **Template conversion** | `proxmox-template-vm` — convert VM to template | Useful for VM lifecycle. Add in Phase 5 |

### 4.3. From JerichoJack/Proxmox-MCP (Low Priority)

| Idea | Why | How to Adapt |
|---|---|---|
| **Event listeners (WebSocket)** | Real-time Proxmox event subscription | Consider for Diagnostic Traversal (Phase 4). Not before |
| **Notification output** | Discord/Gotify/email notifications on infrastructure events | Consider for Operator Mode alerting. Out of scope now |
| **PBS client** | Proxmox Backup Server integration | Consider after Phase 6 |
| **n8n workflow examples** | Demonstrates practical MCP agent workflows | Useful for documentation/community engagement |
| **Topology auto-discovery** | Automatically detect cluster nodes vs manual config | Valuable for configuration UX. Consider post-MVP |

### 4.4. PVE Endpoints Worth Adding Soon

Based on competitor usage, the following PVE API endpoints are most used and should be prioritised:

| Endpoint | Purpose | Priority | Competitors Using |
|---|---|---|---|
| `GET /cluster/tasks` | Task history | High (T-203) | All |
| `GET /nodes/{node}/tasks/{upid}/status` | Task status | High (T-203) | ProxmoxMCP-Plus, bsahane |
| `GET /nodes/{node}/storage/{storage}/content` | Storage content list | High (T-201) | bsahane |
| `GET /nodes/{node}/qemu/{vmid}/config` | VM config | High (T-207) | bsahane |
| `GET /nodes/{node}/lxc/{vmid}/config` | LXC config | High (T-207) | bsahane |
| `GET /nodes/{node}/qemu/{vmid}/rrddata` | VM metrics | Medium (T-207) | bsahane |
| `GET /cluster/options` | Cluster options | Medium | JerichoJack |
| `GET /cluster/resources` | All cluster resources | Medium (T-208) | All |
| `GET /nodes/{node}/disks/list` | Disk info | Medium | ProxmoxMCP-Plus |
| `GET /nodes/{node}/status` | Node status (detailed) | Done | All |

---

## 5. Ideas To Reject

### 5.1. Architectural Contradictions

| Idea | Source | Reason to Reject |
|---|---|---|
| **Generic multi-hypervisor framework** | bsahane (Terraform/Ansible abstraction) | Contradicts ADR-0005 (AI Proxmox Operator positioning). We are Proxmox-native. Terraform/Ansible are infrastructure-as-code tools, not AI operator concerns |
| **"Workload" abstraction** | Common in multi-cloud tools | ADR-0010 explicitly separates VM (QEMU) and LXC as distinct kinds. Workload abstraction erases Proxmox-specific semantics |
| **Monolithic single-file architecture** | JerichoJack, ProxmoxMCP-Plus | Our layered architecture with domain isolation is a strength. Monoliths prevent independent evolution of Read → Diagnostics → Operator layers |
| **Remove policy engine for simplicity** | All competitors (none have one) | Policy engine is our core differentiator. Essential for safe Operator Mode. Removing it would make us "just another MCP server" |

### 5.2. Implementation Patterns to Reject

| Idea | Source | Reason to Reject |
|---|---|---|
| **`proxmoxer` library** | JerichoJack, ProxmoxMCP-Plus, bsahane | Synchronous library wrapped in async. Blocks event loop. Our `httpx.AsyncClient` is architecturally superior |
| **Synchronous `time.sleep()` polling** | bsahane (`wait_task`) | Blocks the async event loop. Use `asyncio.sleep()` or `asyncio.wait_for()` with proper timeout |
| **Bare `except:` blocks** | bsahane (throughout) | Masks errors, makes debugging impossible. Our typed error hierarchy is correct |
| **Hardcoded default passwords** | bsahane (`"changeMe123!"` for LXC) | Security anti-pattern. Fail hard on missing config |
| **Simulated/mock data modules** | bsahane (`ai_optimization.py`, `monitoring.py`) | Misleading for operators. If we implement monitoring/AI, use real data |
| **75+ dependencies for stub modules** | bsahane (`requirements.txt`) | Bloated dependency tree. Keep dependencies minimal and only for real functionality |
| **Proxmox Backup Server as MCP tool** | JerichoJack | PBS has its own API and security context. Mixing PVE and PBS in one server increases attack surface. Separate integration if needed |
| **VM console command execution via API** | ProxmoxMCP-Plus (`execute_vm_command`) | Requires QEMU Guest Agent. Fragile and VM-dependent. Better to document as external tooling |
| **Email/Syslog protocol servers** | JerichoJack (email polling, syslog UDP server) | Adds significant attack surface. Proxmox already has notification system. Duplicate effort |

### 5.3. Features That Conflict With Roadmap

| Feature | Source | Why Not Now |
|---|---|---|
| **Multi-cluster routing** | bsahane | Our architecture targets single-cluster first. Multi-cluster belongs in Phase 4+ (Diagnostic Traversal). Premature complexity |
| **MFA/Vault/certificate management** | bsahane (`security.py`) | Proxmox already handles authentication. We trust the API token. Adding MFA/Vault to the MCP server mixes concerns |
| **Full IaC integration** | bsahane (`infrastructure.py`) | Terraform/Ansible are complementary, not competitive. Our domain is AI infrastructure operator, not CI/CD pipeline |
| **Prometheus/Grafana stack deployment** | bsahane (`monitoring.py`) | Out of scope for an AI operator. Proxmox already integrates with external monitoring. Focus on reading metrics, not deploying stacks |
| **Docker Swarm orchestration** | bsahane (`docker_swarm.py`) | Running Docker inside Proxmox is a tenant concern, not an infrastructure operator concern |
| **RHCOS/OKD/OpenShift config** | bsahane (`rhcos.py`) | Overly specialised. Adds complexity for marginal value. Better as plugin/extension |
| **SSH-based container commands** | ProxmoxMCP-Plus | Useful but introduces significant security surface. Consider only after core mutation lifecycle is solid (Phase 5+) |

---

## 6. Feature Gap Analysis

### 6.1. Current Status vs Competitor Minimum

| Feature Category | Us (Current) | ProxmoxMCP-Plus (Benchmark) | Gap |
|---|---|---|---|
| **Read — Cluster** | `cluster_info` | `get_cluster_status` | ✅ Equivalent |
| **Read — Nodes** | `list_nodes`, `node_status` | `get_nodes`, `get_node_status` | ✅ Equivalent |
| **Read — VMs** | `vm_list`, `vm_status` | `get_vms` | ✅ Equivalent (we have more detail) |
| **Read — LXCs** | `container_list`, `container_status` | `get_containers` | ✅ Equivalent |
| **Read — Storage** | `storage_list`, `storage_status` | `get_storage` | ✅ Equivalent |
| **Read — Network** | `network_list` | None (JerichoJack has it) | ✅ We lead |
| **Read — Backups** | ❌ Planned (T-206) | `list_backups` | ❌ Gap |
| **Read — Snapshots** | ❌ Not planned yet | `list_snapshots` | ❌ Gap |
| **Read — Tasks** | ❌ Planned (T-203) | `get_node_tasks` (JerichoJack) | ❌ Gap |
| **Read — Task Status** | ❌ Planned (T-203) | `get_job`, `poll_job` | ❌ Gap |
| **Read — VM Config** | ❌ Planned (T-207) | Available in bsahane | ❌ Gap |
| **Read — LXC Config** | ❌ Planned (T-207) | Available in bsahane | ❌ Gap |
| **Read — Storage Content** | ❌ Planned (T-201) | Available in bsahane | ❌ Gap |
| **Read — Metrics** | ❌ Planned (T-207) | Available in bsahane | ❌ Gap |
| **Read — Logs** | ❌ Planned (T-204) | None in competitors | ✅ Opportunity |
| **Read — Syslog/Journal** | ❌ Planned (T-204) | None in competitors | ✅ Opportunity |
| **Write — VM Start/Stop** | ❌ Phase 5 | ✅ ProxmoxMCP-Plus | ❌ Gap |
| **Write — VM Create** | ❌ Phase 5 | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — VM Delete** | ❌ Phase 5 | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — LXC Start/Stop** | ❌ Phase 5 | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — LXC Create** | ❌ Phase 5 | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — LXC Delete** | ❌ Phase 5 | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — Snapshot** | ❌ Not planned | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — Backup** | ❌ Not planned | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — Restore** | ❌ Not planned | ✅ ProxmoxMCP-Plus, bsahane | ❌ Gap |
| **Write — Template** | ❌ Not planned | ✅ bsahane | ❌ Gap |
| **Write — Clone** | ❌ Not planned | ✅ bsahane | ❌ Gap |
| **Write — Migrate** | ❌ Phase 5 | ✅ bsahane | ❌ Gap |
| **Write — Resize Disk** | ❌ Not planned | ✅ bsahane | ❌ Gap |
| **Write — NIC** | ❌ Not planned | ✅ bsahane | ❌ Gap |
| **Persistent Jobs** | ❌ Not planned | ✅ ProxmoxMCP-Plus | ❌ Gap |
| **Transport: HTTP** | ❌ Planned (backlog) | ✅ ProxmoxMCP-Plus | ❌ Gap |
| **Transport: SSE** | ❌ Planned (backlog) | ❌ None | ✅ No gap |
| **Docker deployment** | ✅ Basic (Dockerfile + compose) | ✅ Production-grade | ⚠️ Can improve |
| **CI/CD** | ✅ Basic (ruff + pytest) | ✅ Full (CI, coverage, audit) | ⚠️ Can improve |

### 6.2. Where We Lead

1. **Architecture quality** — Layered, typed, testable. No competitor matches our separation of concerns.
2. **Policy engine** — `ToolTier` + `PolicyEngine` is unique. Enables safe path from READ_ONLY → OPERATOR → ADMIN.
3. **Async HTTP client** — `httpx.AsyncClient` is natively async. All competitors use synchronous `proxmoxer`.
4. **Response models** — Pydantic DTOs with `extra="ignore"` for forward compatibility. Competitors use raw dicts.
5. **Error hierarchy** — Per-layer typed exceptions. Competitors use generic `Exception`.
6. **Structured logging** — JSON formatter with correlation IDs and secret redaction. No competitor has this.
7. **Configuration validation** — JSON Schema validation + Pydantic strict models. No competitor validates config.
8. **Test coverage** — 12 unit test files, 25+ tests. Most competitors have zero tests.
9. **Documentation** — ADR records, architecture docs, detailed roadmaps. ~4,000 lines of docs vs ~1,200 of code.
10. **Updates listing** — `node_updates` tool is unique. No competitor lists available APT updates.

### 6.3. Where We Lag

1. **Mutation capabilities** — Zero write tools. All competitors have at least VM/LXC start/stop.
2. **UPID/task handling** — No task polling, no persistent job store, no retry/cancel.
3. **Backup and snapshot** — No read or write capabilities.
4. **Storage content** — Cannot list ISOs/templates on storage.
5. **VM/LXC config** — Cannot read full guest configuration.
6. **HTTP transport** — stdio-only limits deployment options.
7. **Multi-cluster** — Single-cluster only.
8. **Guest command execution** — No SSH or QGA integration.
9. **Integration examples** — No Cursor/VS Code/Claude examples in README.
10. **Community traction** — Others have PyPI packages, Docker pulls, stars.

---

## 7. Recommendations

### 7.1. Immediate Priority (After Infrastructure Read Layer)

These are the features that should be implemented immediately after completing the current Infrastructure Read Layer (Phase 1A). They represent the minimum viable feature set to be competitive while staying true to our architecture.

| # | Feature | Why Now | Effort |
|---|---|---|---|
| 1 | **Task domain (T-203)** — UPID parsing, task list, task status, task log | Required for any mutation. All mutations return UPIDs. Without task handling, we cannot provide feedback on operations | Medium |
| 2 | **Storage content listing (T-201)** — List ISOs, templates, container templates on storage | Required before VM/LXC creation (need to see available templates). Also useful for diagnostic queries | Small |
| 3 | **VM/LXC config reading (T-207)** — Full `/config` endpoint for both QEMU and LXC | Critical for diagnostic traversal. Competitors have it. Needed for "what is this VM configured as?" queries | Small |
| 4 | **Cluster resources (T-208)** — Aggregated view of all cluster resources | `GET /cluster/resources` is the most efficient way to get full inventory. Reduces N+1 queries | Small |

### 7.2. Phase 1B Priority

| # | Feature | Why | Effort |
|---|---|---|---|
| 5 | **Persistent job store** — SQLite-backed job tracking with `job_id` + `task_id` | Foundation for Operator Mode. Enables retry/cancel/audit. Borrow from ProxmoxMCP-Plus design | Medium |
| 6 | **Log domain (T-204)** — Syslog/journal reading from nodes | Unique capability. No competitor provides Proxmox log access via MCP | Medium |
| 7 | **Backup list + job status (T-206)** — List backups, list backup jobs, status | Required diagnostic coverage before mutation phase | Small |
| 8 | **Pagination support** — `limit`/`offset` on list tools | Prevents token overflow for large clusters. All tools return everything now | Small |

### 7.3. Phase 2+ Strategic Priorities

| # | Feature | Phase | Why |
|---|---|---|---|
| 9 | **Confirm + dry-run guard** | Phase 5 | Required before any mutation tool can be safely exposed |
| 10 | **VM/LXC start/stop/restart** | Phase 5 | Minimum mutation capability. All competitors have it |
| 11 | **Snapshot create/rollback/list** | Phase 5 | Safety net for mutation operations. "Create snapshot before upgrade" workflow |
| 12 | **VM/LXC create from template** | Phase 5 | Most requested feature. Enables "create a test VM" workflow |
| 13 | **Streamable HTTP transport** | Phase 2+ | Enables remote deployment. Required for Docker-native MCP |
| 14 | **Backup create/restore** | Phase 5+ | Complete backup workflow |
| 15 | **ISO download/delete** | Phase 5+ | Useful for template management |

### 7.4. Things NOT To Prioritise

- Multi-cluster routing (wait for Phase 4+)
- SSH-based guest command execution (wait for Phase 5+, only if demand exists)
- CloudInit ISO generation (nice-to-have for VM create, not blocking)
- OpenAPI bridge (wait for Operator Mode REST needs)
- Event listeners / WebSocket subscriptions (wait for Diagnostic Traversal Phase 4)
- Windows/RHCOS/Docker Swarm specific configurators (out of scope)
- Prometheus/Grafana stack deployment (out of scope)
- MFA/Vault/certificate management (out of scope)

### 7.5. Key Architectural Decisions to Preserve

1. **Policy engine as mandatory gate** — Keep `PolicyEngine.authorize()` even when mode is `READ_ONLY`. This ensures mutation support doesn't require refactoring.
2. **Async httpx client** — Do NOT switch to `proxmoxer`. Our architecture is natively async. The sync-in-async pattern of competitors is a genuine weakness.
3. **Domain isolation** — Keep read-only tools in their own domain modules. Mutation tools will go in adjacent files, not mixed in.
4. **Tool tiers** — Every tool must have a `ToolTier`. This is what enables safe incremental rollout from READ_ONLY → OPERATOR → ADMIN.
5. **Typed errors** — Continue the typed error hierarchy. No bare `except:` blocks.
6. **EntityRef system (ADR-0007)** — Implement for tasks, VMs, LXCs, storage. Provides universal reference format across Memory, Dependencies, Audit.

### 7.6. Quick Wins From Competitors

| Quick Win | Source | Implementation |
|---|---|---|
| Add `confirm=true` parameter schema to all tools (even if ignored in READ_ONLY) | ProxmoxMCP-Plus | Future-proofs tool schemas. Clients can start sending `confirm` now |
| Rename tools to `pve_*` prefix for consistency with docs | Ours | Docs specify `pve_cluster_info`, code uses `cluster_info`. Align naming |
| Add `server_info` metadata (version, available tools, policy mode) | Done already | We already have this. Verify it works in test harness |
| Improve `--help` output for CLI entry point | All competitors | Currently minimal. Add examples, config path hints |
| Publish to PyPI | ProxmoxMCP-Plus | Enables `uvx mcp-proxmox` one-liner install. Significant for adoption |

---

*This analysis was conducted on 2026-06-05. The MCP ecosystem for Proxmox evolves rapidly — recommendations should be revisited quarterly.*
