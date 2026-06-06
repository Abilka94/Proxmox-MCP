# MCP-Proxmox

AI Infrastructure Operator for Proxmox VE, exposed as a Model Context Protocol (MCP) server.

---

## Current Status

| Параметр | Значение |
|----------|----------|
| Current Version | `v0.3.0-phase1b.2` |
| Latest Accepted Milestone | **Phase 1B.2** — Task Domain Extended |
| Primary Target | PVE 9.x |
| Secondary Target | PVE 8.x (best effort, node-level fallback) |
| Test Status | **135/135** tests passing |
| Live Validation | PVE 9.2.3 cluster (3 nodes, quorate) ✅ |

---

## Features

### Cluster
- Cluster status, quorum, node membership

### Nodes
- Node list with online/offline status
- Node resource usage (CPU, memory, disk, uptime)

### Virtual Machines
- VM inventory with resource allocation
- VM runtime status (CPU, memory, disk I/O, balloon)
- VM configuration

### Containers (LXC)
- Container inventory
- Container runtime status
- Container configuration

### Storage
- Storage pool inventory
- Storage status and usage
- Storage content listing

### Network
- Network interface listing per node

### Updates
- Per-node available package updates
- Cluster-wide aggregated update view

### Tasks
- Task list with filtering (status, type, user, VMID)
- Task status (UPID → status, exit status)
- Task log (incremental, with start offset)
- `task_wait` — poll until completion with configurable timeout and exponential backoff
- `task_follow` — poll with incremental log accumulation (max 5000 lines)

---

## MCP Tools

**21 tools** across 9 domains.

### Cluster
- `server_info` — server identity and configuration
- `cluster_info` — cluster status and quorum

### Nodes
- `list_nodes` — list all nodes with status
- `node_status` — detailed node resource usage

### VMs
- `vm_list` — VM inventory
- `vm_status` — VM runtime status
- `vm_config` — VM configuration

### Containers
- `container_list` — LXC container inventory
- `container_status` — container runtime status
- `container_config` — container configuration

### Storage
- `storage_list` — storage pool inventory
- `storage_status` — storage usage and status
- `storage_content` — storage content listing

### Network
- `network_list` — network interfaces per node

### Updates
- `node_updates` — available updates on a node
- `cluster_updates` — aggregated cluster-wide updates

### Tasks
- `task_list` — task history with filters
- `task_status` — task status by UPID
- `task_log` — task log output
- `task_wait` — wait for task completion (timeout, backoff)
- `task_follow` — wait with incremental log accumulation

---

## Roadmap

- [x] **Phase 1A** — MCP + PVE Core Read (cluster, nodes, VMs, containers, storage, network)
- [x] **Phase 1B.1** — Task Domain Core (task_list, task_status, task_log, node-level updates)
- [x] **Phase 1B.2** — Task Domain Extended (task_wait, task_follow, polling, log accumulation)
- [ ] **Phase 1C** — Task Mutate (task_cancel, task_stop, POST operations)
- [ ] **Phase 2** — Knowledge Foundation (Memory, EntityRef, annotations)
- [ ] **Phase 3** — Service Layer (service-to-resource mapping)
- [ ] **Phase 4** — Diagnostic Operator (service-aware health checks)
- [ ] **Phase 5** — Controlled Actions (policy-gated mutate operations)

---

## Documentation

### Index
- [docs/README.md](docs/README.md) — полный индекс документации проекта

### Architecture & Design
- [Architecture](docs/architecture/ARCHITECTURE.md) — runtime, MCP, Policy, Domains, tiers
- [ADR Index](docs/adr/ADR_INDEX.md) — архитектурные решения (ADR-0001–ADR-0010)
- [Reference Usage Policy](docs/architecture/REFERENCE_USAGE_POLICY.md) — порядок использования reference-репозиториев
- [Implementation Roadmap](docs/releases/IMPLEMENTATION_ROADMAP.md) — фазы 1A–6, MVP (v1.0)

### Accepted Milestones

**Phase 1A** — Infrastructure Read Layer (v0.1.0)
- [Design & Reports](docs/phase-1a/) — 9 документов
- [Validation](docs/phase-1a/validation/) — 4 документа
- [Acceptance](docs/phase-1a/acceptance/) — 1 документ

**Phase 1B.1** — Task Domain Core (v0.2.0)
- [Design](docs/phase-1b/phase-1b.1/design/) — design document
- [Implementation](docs/phase-1b/phase-1b.1/implementation/) — implementation report
- [Validation](docs/phase-1b/phase-1b.1/validation/) — 4 документа
- [Acceptance](docs/phase-1b/phase-1b.1/acceptance/) — 1 документ

**Phase 1B.2** — Task Domain Extended (v0.3.0)
- [Design](docs/phase-1b/phase-1b.2/design/) — design document
- [Implementation](docs/phase-1b/phase-1b.2/implementation/) — implementation report + validation plan
- [Validation](docs/phase-1b/phase-1b.2/validation/) — connectivity check + validation report
- [Acceptance](docs/phase-1b/phase-1b.2/acceptance/) — 1 документ

### Historical Documents
- [Archive](docs/archive/) — codebase audit, competitive analysis, documentation audit, reference usage audit, README refresh

---

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit
python -m ruff check src/ tests/
python -m mypy src/
```

---

## Project Status

**Stable Development.** Active development with regular releases. All milestone features are validated against live PVE clusters before acceptance.
