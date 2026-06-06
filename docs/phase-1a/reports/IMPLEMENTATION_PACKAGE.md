# Implementation Package — Phase 1A Start

**Версия:** 1.0  
**Дата:** 2026-06-03  
**Статус:** Active — руководство к началу разработки  
**Фаза:** Phase 1A ([IMPLEMENTATION_ROADMAP.md](../IMPLEMENTATION_ROADMAP.md))

**Нормативная база:** [ARCHITECTURE.md](../ARCHITECTURE.md) v0.2, [MEMORY_KNOWLEDGE_MODEL.md](../MEMORY_KNOWLEDGE_MODEL.md) v1.0, ADR [0005](../adr/0005-ai-proxmox-operator-positioning.md)–[0010](../adr/0010-service-type-taxonomy.md).

**Связанные документы:**

- [ADR-0001 (draft)](../adr/0001-implementation-language.md) — язык  
- [ADR-0002 (draft)](../adr/0002-mcp-transport.md) — транспорт  
- [PHASE_1A_TASK_PLAN.md](PHASE_1A_TASK_PLAN.md) — задачи T-000…T-117  
- [DOCUMENTATION_AUDIT.md](../audit/DOCUMENTATION_AUDIT.md)  
- [DOCUMENTATION_CLEANUP_PLAN.md](../audit/DOCUMENTATION_CLEANUP_PLAN.md)

---

## 1. Рекомендуемый язык реализации

**Python 3.12+**

Окончательное решение — после принятия [ADR-0001](../adr/0001-implementation-language.md).

---

## 2. Обоснование выбора

| Критерий | Python | TypeScript (альтернатива) |
|----------|--------|---------------------------|
| Официальный MCP SDK | `mcp` (Python SDK) — зрелый | `@modelcontextprotocol/sdk` — зрелый |
| HTTP к PVE (fan-out, async) | `httpx` async — простая модель | `fetch` / undici — хорошо |
| SQLite (Phase 2+) | stdlib + aiosqlite | better-sqlite3 |
| Скрипты каталога tools | уже заложены в ARCHITECTURE | отдельный tooling |
| Контрактные тесты / snapshots | pytest + JSON | vitest + JSON |
| Порог входа для OSS | низкий для homelab/admin | выше (build chain) |
| Типизация | Pydantic v2 | нативная TS |

**Вывод:** для MCP-сервера с упором на интеграцию, async I/O к нескольким нодам и последующий SQLite Knowledge — **Python** минимизирует time-to-first-working-operator (Phase 1A) без компромисса по архитектуре.

**Не влияет на архитектуру:** модули `src/` остаются language-agnostic по границам из ARCHITECTURE §4.

---

## 3. Структура репозитория

Монорепозиторий, один deployable MCP-сервер:

| Область | Назначение |
|---------|------------|
| `src/mcp_proxmox/` | Код оператора (Python package) |
| `config/` | Примеры и JSON Schema конфигурации |
| `deploy/` | Docker, compose, примеры MCP-клиента |
| `tests/` | unit, contract, integration |
| `docs/` | Нормативная и проектная документация |
| `scripts/` | dev-утилиты (catalog, validate-config) |
| `data/` | runtime (gitignored) |

---

## 4. Дерево каталогов (целевое для Phase 1A)

```
MCP-Proxmox/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/
│   ├── default.yaml
│   └── schema/
│       └── config.schema.json
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── mcp-client.example.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── MEMORY_KNOWLEDGE_MODEL.md
│   ├── IMPLEMENTATION_ROADMAP.md
│   ├── TOOL_CATALOG.md              # генерируется позже
│   ├── OPERATIONS.md                # draft Phase 1B
│   ├── implementation/
│   │   ├── IMPLEMENTATION_PACKAGE.md
│   │   └── PHASE_1A_TASK_PLAN.md
│   ├── audit/
│   │   ├── DOCUMENTATION_AUDIT.md
│   │   └── DOCUMENTATION_CLEANUP_PLAN.md
│   ├── adr/
│   │   ├── ADR_INDEX.md
│   │   ├── template.md
│   │   ├── 0001-implementation-language.md
│   │   ├── 0002-mcp-transport.md
│   │   └── 0005…0010 (accepted)
│   └── archive/                     # после cleanup
├── scripts/
│   ├── validate_config.py
│   └── generate_tool_catalog.py     # Phase 1B
├── src/
│   └── mcp_proxmox/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config/
│       ├── logging/
│       ├── mcp/
│       │   ├── transport/
│       │   ├── registry/
│       │   ├── session/
│       │   └── handlers/
│       ├── policy/
│       ├── pve/
│       │   ├── client/
│       │   ├── auth/
│       │   └── models/
│       ├── orchestrator/
│       ├── domains/
│       │   ├── cluster/
│       │   ├── nodes/
│       │   ├── containers/
│       │   └── vms/
│       ├── cache/
│       └── audit/
├── tests/
│   ├── unit/
│   ├── contract/
│   │   ├── fixtures/
│   │   └── snapshots/
│   └── integration/
│       └── mock_pve/
└── data/
    └── .gitkeep
```

Модули `knowledge/`, `memory/`, остальные `domains/*` — **пустые placeholder или отсутствуют** до соответствующих фаз (не создавать реализацию в 1A).

---

## 5. Основные зависимости (runtime)

| Пакет | Назначение | Phase |
|-------|------------|-------|
| `mcp` | MCP server SDK (stdio) | 1A |
| `httpx` | Async HTTP client к PVE | 1A |
| `pydantic` | Config, DTO, tool I/O | 1A |
| `pydantic-settings` | Env + file config | 1A |
| `pyyaml` | YAML config | 1A |
| `structlog` | Structured logging | 1A |
| `anyio` | Async runtime (transitive / explicit) | 1A |
| `aiosqlite` | Memory store | 2+ |
| `jsonschema` | Service validation (optional strict) | 3+ |

Версии фиксируются в `pyproject.toml` с upper bounds; точные pin — при T-004.

---

## 6. Dev-зависимости

| Пакет | Назначение |
|-------|------------|
| `pytest` | Unit / integration |
| `pytest-asyncio` | Async tests |
| `pytest-cov` | Coverage |
| `ruff` | Lint + format |
| `mypy` | Static types (strict на `src/`) |
| `pre-commit` | Hooks (optional, T-004) |
| `respx` или `pytest-httpx` | Mock HTTP PVE |

---

## 7. Формат конфигурации

### 7.1 Источники (приоритет, высший последним)

1. `config/default.yaml`  
2. `config/local.yaml` (optional, gitignored)  
3. Environment variables (`MCP_PROXMOX_*` или префикс из ADR)

### 7.2 Структура (согласована с ARCHITECTURE §12.2)

```yaml
connection:
  id: "dc-prod"                    # cluster_id для Memory (Phase 2+)
  host: "https://pve.example.local:8006"
  token_id: "${PVE_TOKEN_ID}"
  token_secret: "${PVE_TOKEN_SECRET}"
  verify_ssl: true

policy:
  mode: READ_ONLY
  memory:
    allow_write: true               # Phase 2+; игнорируется в 1A

orchestrator:
  max_concurrent_per_node: 5
  max_concurrent_cluster: 15
  node_request_timeout_sec: 30
  aggregate_threshold: 500          # Phase 1B

cache:
  cluster_resources_ttl_sec: 30
  node_status_ttl_sec: 15

logging:
  level: INFO
  format: json                      # json | console

audit:
  path: "data/audit.log"

subsystems:
  logs:
    enabled: true
    max_lines: 500
```

### 7.3 Валидация

- JSON Schema: `config/schema/config.schema.json`  
- CLI: `scripts/validate_config.py` (T-100)  
- Секреты **только** через env, не в committed YAML

---

## 8. Формат логирования

| Аспект | Решение |
|--------|---------|
| Библиотека | `structlog` |
| Production | JSON lines → stdout (Docker-friendly) |
| Development | `format: console` в config |
| Correlation | `correlation_id` на каждый MCP request; пробрасывать в PVE sub-requests как `pve_request_id` / header log field |
| Уровни | INFO — tool calls; DEBUG — HTTP path/status (без token); WARNING — partial node failure |
| Audit | Отдельный append-only `data/audit.log` (не смешивать с app log) |

Пример полей JSON log:

```json
{
  "event": "tool_call",
  "correlation_id": "…",
  "tool": "pve_nodes_list",
  "duration_ms": 42,
  "outcome": "ok"
}
```

---

## 9. Подход к тестированию

### 9.1 Пирамида

| Уровень | Каталог | Phase 1A |
|---------|---------|----------|
| **Unit** | `tests/unit/` | client, policy, pagination, config, EntityRef позже |
| **Contract** | `tests/contract/` | JSON snapshot ответов 8 tools 1A |
| **Integration** | `tests/integration/` | mock PVE multi-node (T-005 fixture) |
| **E2E manual** | README | Cursor / MCP Inspector + реальный PVE optional |

### 9.2 Mock PVE (T-005)

- HTTP fixture: `tests/integration/mock_pve/`  
- Сценарии: standalone 1 node; 3 nodes; pagination; 404 guest; node timeout  
- Формат: статические JSON ответы + `respx` routes или локальный `pytest-httpserver`

### 9.3 Contract tests

- Один файл snapshot на tool  
- Стабильная нормализация (sorted keys, redact token)  
- CI: `pytest tests/contract tests/unit tests/integration`

### 9.4 Coverage (ориентир Phase 1A)

- `src/mcp_proxmox/pve/`, `policy/`, `orchestrator/` — ≥ 80%  
- Handlers — через integration + contract

### 9.5 CI (T-004 skeleton)

- GitHub Actions / Gitea Actions: lint (ruff), typecheck (mypy), pytest  
- Без live PVE в CI

---

## 10. Entrypoint и запуск (концепт)

| Режим | Команда (после T-004) |
|-------|------------------------|
| Dev | `python -m mcp_proxmox` (stdio) |
| Config check | `python scripts/validate_config.py` |
| Docker | `docker compose up mcp-proxmox` |

---

## 11. Чеклист готовности к Phase 1A code

- [ ] ADR-0001 accepted  
- [ ] ADR-0002 accepted  
- [ ] T-003 done (ARCHITECTURE v0.2)  
- [ ] T-004 repo skeleton  
- [ ] T-005 mock PVE  
- [ ] Documentation cleanup по [DOCUMENTATION_CLEANUP_PLAN.md](../audit/DOCUMENTATION_CLEANUP_PLAN.md)

---

## 12. Следующий документ

Детальный план задач: [PHASE_1A_TASK_PLAN.md](PHASE_1A_TASK_PLAN.md).
