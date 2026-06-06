# Phase 1A — Детальный план задач (T-000 … T-117)

**Версия:** 1.0  
**Дата:** 2026-06-03  
**Источник:** [IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md) §13  
**Пакет:** [IMPLEMENTATION_PACKAGE.md](IMPLEMENTATION_PACKAGE.md)

Легенда статуса: `done` — выполнено; `in_progress` — начато, DoD ещё не закрыт; `ready` — готово к выполнению; `blocked` — ждёт зависимости.

---

## §13.0 Подготовка (T-000 … T-005)

### T-000 — Принять ADR-0001 (язык реализации)

| Поле | Значение |
|------|----------|
| **Назначение** | Зафиксировать Python 3.12+ как язык v1 |
| **Зависимости** | — |
| **Результат** | ADR-0001 status = **accepted**; ADR_INDEX обновлён |
| **DoD** | [x] ADR-0001 accepted; [x] IMPLEMENTATION_PACKAGE согласован; [x] T-004 может стартовать |

**Статус:** **done**

---

### T-001 — Принять ADR-0002 (MCP Transport)

| Поле | Значение |
|------|----------|
| **Назначение** | stdio — primary transport Phase 1A; SSE — backlog |
| **Зависимости** | T-000 (рекомендуется) |
| **Результат** | ADR-0002 accepted |
| **DoD** | [x] ADR-0002 accepted; [x] ARCHITECTURE §3.2 не противоречит |

**Статус:** **done**

---

### T-002 — Принять ADR-0003 (memory.allow_write)

| Поле | Значение |
|------|----------|
| **Назначение** | Default `memory.allow_write=true` при READ_ONLY для локальной Memory (Phase 2) |
| **Зависимости** | ADR-0006, 0007 (accepted) |
| **Результат** | ADR-0003 accepted или явный default в config schema без ADR |
| **DoD** | [ ] Решение задокументировано; [ ] config/default.yaml содержит секцию (можно в T-100) |

**Статус:** ready (не блокирует 1A code)

---

### T-003 — Синхронизировать ARCHITECTURE.md v0.2

| Поле | Значение |
|------|----------|
| **Назначение** | Единый верхнеуровневый архитектурный документ |
| **Зависимости** | MEMORY v1.0, ADR 0005–0010 |
| **Результат** | ARCHITECTURE.md v0.2 + §16 Consistency Report |
| **DoD** | [x] Принят заказчиком |

**Статус:** **done**

---

### T-004 — Скелет репозитория

| Поле | Значение |
|------|----------|
| **Назначение** | Структура каталогов, pyproject.toml, CI skeleton, LICENSE, README stub |
| **Зависимости** | T-000 |
| **Результат** | Дерево из IMPLEMENTATION_PACKAGE §4; пустые `__init__.py`; локальные lint+test команды |
| **DoD** | [ ] `pip install -e ".[dev]"` работает; [ ] `pytest` (0 tests) green; [ ] ruff/mypy локально |

**Статус:** in_progress (skeleton создан; `pip install -e ".[dev]"`, `pytest`, `ruff`, `mypy` требуют dev-окружение)

---

### T-005 — Mock PVE HTTP fixture

| Поле | Значение |
|------|----------|
| **Назначение** | Тестовый двойник PVE API: multi-node, pagination, errors |
| **Зависимости** | T-004 (каталог tests/) |
| **Результат** | `tests/integration/mock_pve/` + JSON fixtures; helper для pytest |
| **DoD** | [ ] Сценарии: 1 node, 3 nodes, guest 404, node timeout; [ ] Документирован запуск в tests/README |

**Статус:** blocked → T-004

---

## §13.1 Phase 1A Core (T-100 … T-117)

### T-100 — Config loader + schema validation

| Поле | Значение |
|------|----------|
| **Назначение** | Загрузка YAML + env; валидация Pydantic/JSON Schema |
| **Зависимости** | T-004 |
| **Результат** | `mcp_proxmox.config`; `config/default.yaml`; `scripts/validate_config.py` |
| **DoD** | [x] Invalid config → exit code ≠ 0; [x] Secrets только из env; [x] Unit tests |

**Статус:** **done**

---

### T-101 — Structured logging + correlation id

| Поле | Значение |
|------|----------|
| **Назначение** | structlog JSON/console; correlation_id на MCP request |
| **Зависимости** | T-100 |
| **Результат** | `mcp_proxmox.logging`; middleware hook для handlers |
| **DoD** | [x] JSON log содержит correlation_id; [x] Token не логируется |

**Статус:** **done**

---

### T-102 — PVE HTTP client

| Поле | Значение |
|------|----------|
| **Назначение** | httpx async, PVEAPIToken, retry, TLS, `PveApiError` |
| **Зависимости** | T-100, T-101 |
| **Результат** | `mcp_proxmox.pve.client`, `auth`, базовые `models` |
| **DoD** | [ ] Unit tests с respx; [ ] 401/500 mapping; [ ] verify_ssl из config |

---

### T-103 — Policy Engine

| Поле | Значение |
|------|----------|
| **Назначение** | READ_ONLY; tier READ на registry; PolicyDenied для OPERATOR stub |
| **Зависимости** | T-100 |
| **Результат** | `mcp_proxmox.policy.engine`, tiers enum |
| **DoD** | [x] Unit tests: READ allowed; OPERATOR denied; [x] policy.mode из config |

**Статус:** **done**

---

### T-104 — Tool Registry + MCP stdio server

| Поле | Значение |
|------|----------|
| **Назначение** | Регистрация tools; запуск MCP stdio (ADR-0002) |
| **Зависимости** | T-001, T-103 |
| **Результат** | `mcp_proxmox.mcp.registry`, `transport/stdio`, `__main__.py` |
| **DoD** | [ ] MCP Inspector list_tools; [ ] Пустой handler отвечает; [ ] Graceful shutdown |

---

### T-105 — Session context

| Поле | Значение |
|------|----------|
| **Назначение** | session_id, connection id (cluster_id), actor placeholder |
| **Зависимости** | T-104 |
| **Результат** | `mcp_proxmox.mcp.session`; contextvar для correlation |
| **DoD** | [ ] Session доступен в handlers; [ ] Unit test context propagation |

---

### T-106 — Orchestrator

| Поле | Значение |
|------|----------|
| **Назначение** | Discovery nodes; fan-out; semaphore; partial_results; pagination helpers |
| **Зависимости** | T-102, T-105 |
| **Результат** | `mcp_proxmox.orchestrator` |
| **DoD** | [ ] Mock 3 nodes → aggregated list; [ ] One node fail → errors[]; [ ] Limits из config |

---

### T-107 — Domain Cluster

| Поле | Значение |
|------|----------|
| **Назначение** | `pve_cluster_status`, `pve_cluster_resources` |
| **Зависимости** | T-102, T-106 |
| **Результат** | `domains/cluster/` + handlers |
| **DoD** | [ ] Contract snapshot; [ ] pagination на resources |

---

### T-108 — Domain Node

| Поле | Значение |
|------|----------|
| **Назначение** | `pve_nodes_list`, `pve_node_status` |
| **Зависимости** | T-106, T-107 |
| **Результат** | `domains/nodes/` |
| **DoD** | [ ] Contract tests; [ ] limit/offset |

---

### T-109 — Domain LXC

| Поле | Значение |
|------|----------|
| **Назначение** | `pve_lxc_list`, `pve_lxc_status` |
| **Зависимости** | T-106, T-108 |
| **Результат** | `domains/containers/` |
| **DoD** | [ ] Guest id `node:vmid` в ответе; [ ] Contract tests |

---

### T-110 — Domain VM (QEMU)

| Поле | Значение |
|------|----------|
| **Назначение** | `pve_qemu_list`, `pve_qemu_status` |
| **Зависимости** | T-106, T-108 |
| **Результат** | `domains/vms/` |
| **DoD** | [ ] Аналогично T-109 для qemu |

---

### T-111 — MCP handlers wire-up

| Поле | Значение |
|------|----------|
| **Назначение** | Связать 8 tools 1A: policy → orchestrator → domain |
| **Зависимости** | T-104, T-107–T-110 |
| **Результат** | `mcp/handlers/tools.py` (или per-domain) |
| **DoD** | [ ] Все 8 tools вызываемы из MCP; [ ] Input schema Pydantic |

---

### T-112 — Audit JSON-lines

| Поле | Значение |
|------|----------|
| **Назначение** | Append-only audit.log: tool, tier, session, outcome |
| **Зависимости** | T-105, T-111 |
| **Результат** | `mcp_proxmox.audit` |
| **DoD** | [ ] Запись на каждый tool call; [ ] Path из config |

---

### T-113 — Unit tests (core)

| Поле | Значение |
|------|----------|
| **Назначение** | Покрытие client, policy, pagination, orchestrator |
| **Зависимости** | T-102, T-103, T-106 |
| **Результат** | `tests/unit/` |
| **DoD** | [ ] Coverage ≥80% на pve/, policy/, orchestrator/ |

---

### T-114 — Contract tests (8 tools)

| Поле | Значение |
|------|----------|
| **Назначение** | JSON snapshots ответов Phase 1A tools |
| **Зависимости** | T-005, T-111 |
| **Результат** | `tests/contract/snapshots/` |
| **DoD** | [ ] 8 snapshots; [ ] CI stable (redact dynamic fields) |

---

### T-115 — Integration test mock multi-node

| Поле | Значение |
|------|----------|
| **Назначение** | E2E через MCP layer против mock PVE |
| **Зависимости** | T-005, T-111 |
| **Результат** | `tests/integration/test_phase1a.py` |
| **DoD** | [ ] cluster + 3 nodes + guests list; [ ] partial failure case |

---

### T-116 — README quickstart

| Поле | Значение |
|------|----------|
| **Назначение** | Установка, config, Cursor mcp.json, первый tool call |
| **Зависимости** | T-111, T-117 (опционально parallel) |
| **Результат** | Root README.md |
| **DoD** | [ ] ≤15 min path; [ ] .env.example; [ ] Troubleshooting SSL/token |

---

### T-117 — Dockerfile + compose

| Поле | Значение |
|------|----------|
| **Назначение** | Контейнер MCP-only; volume для data/; stdio-friendly |
| **Зависимости** | T-004, T-100 |
| **Результат** | `deploy/Dockerfile`, `docker-compose.yml` |
| **DoD** | [ ] Image builds; [ ] compose up; [ ] Secrets via env file |

---

## §13.2 Phase 1B (T-200 … T-213) — краткий план

| ID | Назначение | Зависимости | Результат | DoD (кратко) |
|----|------------|-------------|-----------|--------------|
| T-200 | Capability discovery | 1A complete | `pve/capabilities.py` | flags; CapabilityUnavailable |
| T-201 | Domain Storage | T-200 | storage tools | contract tests |
| T-202 | Domain Network | T-200, ADR-0004 | network tools | SDN gated |
| T-203 | Domain Task | 1A | task tools | UPID handling |
| T-204 | Domain Logs | 1A | syslog/journal | max_lines cap |
| T-205 | Domain Update | 1A | update tools | — |
| T-206 | Domain Backup | T-200, ADR-0011 | backup tools | gated |
| T-207 | LXC/VM config+rrd | 1A | 4 tools | RRD limits |
| T-208 | Aggregate overview | T-107–110 | overview tools | truncated flag |
| T-209 | MCP Resources | domains | pve:// URIs | read resources |
| T-210 | Cache TTL | T-100 | cache module | per-tool TTL |
| T-211 | TOOL_CATALOG gen | Registry | script + md | committed catalog |
| T-212 | Contract all 1B | T-201–208 | snapshots | CI green |
| T-213 | README PVE 8/9 matrix | ADR-0008 | README section | compatibility table |

---

## §13.3 Phase 2 (T-300 … T-311)

| ID | Назначение | Зависимости | Результат | DoD (кратко) |
|----|------------|-------------|-----------|--------------|
| T-300 | SQLite schema 1.0 | 1A | migrations | schema_version |
| T-301 | EntityRef | T-300, MEMORY §4 | entityref module | validate+URI |
| T-302 | Memory repository | T-300 | store layer | CRUD memories |
| T-303 | Knowledge Service core | T-301–302 | knowledge/ | resolve, search |
| T-304 | pve_memory_* handlers | T-303 | MCP tools | list/search/get |
| T-305 | pve_knowledge_resolve | T-301 | tool | unit tests |
| T-306 | pve_adr_* | T-303 | read docs/adr | list/get |
| T-307 | memory_note_create | T-303, ADR-0003 | tool + policy | allow_write |
| T-308 | Lazy reconcile | T-301, PVE | hook | stale flag |
| T-309 | Memory resources | T-302 | pve://memory/* | MCP resources |
| T-310 | Memory tests | T-304–309 | unit+integration | CI green |
| T-311 | Deploy data volume | T-117 | compose volume | data/ mounted |

---

## §13.4 Phase 3 (T-400 … T-408)

| ID | Назначение | Зависимости | Результат | DoD (кратко) |
|----|------------|-------------|-----------|--------------|
| T-400 | services + edges tables | T-300 | SQLite | migrations |
| T-401 | Service model | T-400, ADR-0010 | pydantic + schema | validation |
| T-402 | pve_service_* CRUD | T-401 | MCP tools | upsert/get/list/delete |
| T-403 | pve_service_link | T-401 | cycle detect | max 32 deps |
| T-404 | RunsOn validation | T-402, PVE | lazy PVE check | RunsOnNotFound |
| T-405 | reconcile on get | T-404 | service get | stale |
| T-406 | audit service.upsert | T-112 | audit events | logged |
| T-407 | resource services | T-402 | pve://memory/services | — |
| T-408 | Service integration tests | T-402–405 | tests | lifecycle+stale |

---

## §13.5 Phase 4 / v1.0.0 (T-500 … T-510)

| ID | Назначение | Зависимости | Результат | DoD (кратко) |
|----|------------|-------------|-----------|--------------|
| T-500 | Traversal BFS | T-303, MEMORY §8 | traverse/ | depth, truncate |
| T-501 | Live state fetcher | T-500, domains | semaphore 16 | — |
| T-502 | suggested_checks | T-500 | templates | no product names |
| T-503 | pve_knowledge_traverse | T-500–502 | MCP tool | contract test |
| T-504 | pve_knowledge_reconcile | T-308 | on_demand | scope param |
| T-505 | snapshot_bookmark | T-504 | reconcile | cluster bookmark |
| T-506 | scheduled reconcile | T-504 | background job | optional v1.0.1 |
| T-507 | E2E playbook script | T-503 | scripts/ | manual checklist |
| T-508 | MCP prompt diagnose | T-503 | prompt | optional |
| T-509 | Release v1.0.0 | all 4.x | tag, CHANGELOG | release notes |
| T-510 | Security pass | 1A–4 | audit doc | SSRF, secrets |

---

## Граф критического пути Phase 1A

```
T-000 → T-004 → T-005
         ↓
T-100 → T-101 → T-102 → T-106 → T-107 → T-108 → T-109 → T-110 → T-111
         ↓              ↑
T-103 → T-104 → T-105 ─┘
         ↓
T-112, T-113, T-114, T-115, T-116, T-117
```

**Параллельно после T-106:** T-109 и T-110; после T-111: T-112–T-117.

---

## Критерий завершения Phase 1A (фаза)

Все DoD T-000, T-001, T-004, T-005, T-100…T-117 выполнены; релиз **`0.1.0-alpha`**; ROADMAP §2.4 DoD.
