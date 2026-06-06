# Codebase Audit Report

> **SUPERSEDED** — This audit reflects the codebase before the async/httpx/MCP-spec technical sprint.
> Key changes since: MCP server implemented with spec-compliant `tools/call`, PVE client migrated from urllib to httpx async,
> full async call chain (server → registry → domain → PVE client), entry point now serves MCP over stdio,
> test count grew from 12 to 25. Refer to `TECHNICAL_DEBT_REMEDIATION_REPORT.md` for current state.

**Дата:** 2026-06-04  
**Режим аудита:** фактическое состояние кода, без продолжения Phase 1A  
**Цель:** отделить реализованный код от skeleton/stub/placeholder и оценить реальную готовность проекта.

---

## 1. Executive Summary

Репозиторий находится в раннем bootstrap-состоянии. Реально реализованы три прикладных слоя:

- Config System: Pydantic-модели, загрузка YAML, env-подстановка, CLI-валидатор.
- Logging: stdlib JSON/console logging, correlation context, redaction секретов.
- Policy Engine: tiers `READ`, `OPERATOR`, `ADMIN` и запрет non-READ в `READ_ONLY`.

Остальные ключевые runtime-части Phase 1A пока являются каркасом:

- MCP server отсутствует.
- PVE HTTP client отсутствует.
- Orchestrator отсутствует.
- Domains отсутствуют.
- Audit/cache отсутствуют.
- Точка входа существует, но выводит bootstrap-сообщение и не запускает MCP.

Фактическое состояние: это уже не только документация, но ещё не работающий MCP-продукт.

---

## 2. File Inventory

Статусы:

- `implemented` — есть рабочая логика, покрытая тестами или явно используемая.
- `partial` — есть полезная часть, но компонент не завершён.
- `skeleton` — структурный каркас без логики.
- `stub` — явная заглушка с временным поведением.
- `placeholder` — файл/каталог-метка или будущий артефакт.
- `empty` — пустой файл.

| Path | Назначение | Lines | Status |
|------|------------|-------|--------|
| `.env.example` | Пример env-секретов и config path | 4 | partial |
| `.gitignore` | Локальные исключения runtime/build артефактов | 17 | implemented |
| `CHANGELOG.md` | Журнал локальных изменений | 8 | partial |
| `CODEBASE_AUDIT_REPORT.md` | Текущий технический аудит | n/a | implemented |
| `LICENSE` | MIT license template | 17 | partial |
| `README.md` | Краткое описание bootstrap-проекта | 19 | partial |
| `pyproject.toml` | Python project metadata, deps, pytest/ruff/mypy config | 48 | partial |
| `config/default.yaml` | Default config с env placeholders | 27 | partial |
| `config/schema/config.schema.json` | JSON Schema конфигурации | 95 | partial |
| `data/.gitkeep` | Placeholder runtime data dir | 0 | placeholder |
| `deploy/Dockerfile` | Minimal container entrypoint | 6 | partial |
| `deploy/docker-compose.yml` | Compose sketch для stdio-friendly container | 12 | partial |
| `deploy/mcp-client.example.json` | Пример MCP client config | 14 | partial |
| `docs/README.md` | Индекс документации | 32 | implemented |
| `docs/ARCHITECTURE.md` | Нормативная архитектура | 474 | implemented |
| `docs/MEMORY_KNOWLEDGE_MODEL.md` | Нормативная memory/knowledge модель | 575 | implemented |
| `docs/IMPLEMENTATION_ROADMAP.md` | Roadmap Phase 1A-6 | 556 | implemented |
| `docs/adr/0001-implementation-language.md` | ADR языка реализации | 50 | implemented |
| `docs/adr/0002-mcp-transport.md` | ADR транспорта MCP | 58 | implemented |
| `docs/adr/0005-ai-proxmox-operator-positioning.md` | ADR positioning | 23 | implemented |
| `docs/adr/0006-two-level-knowledge-model.md` | ADR knowledge layers | 29 | implemented |
| `docs/adr/0007-entityref.md` | ADR EntityRef | 37 | implemented |
| `docs/adr/0008-pve-compatibility-matrix.md` | ADR compatibility | 32 | implemented |
| `docs/adr/0009-scalability-limits.md` | ADR scalability | 37 | implemented |
| `docs/adr/0010-service-type-taxonomy.md` | ADR service taxonomy | 39 | implemented |
| `docs/adr/ADR_INDEX.md` | Индекс ADR | 64 | implemented |
| `docs/adr/template.md` | Template для будущих ADR | 15 | placeholder |
| `docs/archive/README.md` | Описание архива | 7 | implemented |
| `docs/archive/recommendations/ARCHITECTURE_UPDATE_RECOMMENDATIONS.md` | Historical recommendations | 185 | implemented |
| `docs/archive/reviews/ARCHITECTURE_REVIEW_2026-06-03.md` | Historical review | 312 | implemented |
| `docs/audit/DOCUMENTATION_AUDIT.md` | Аудит документации | 99 | implemented |
| `docs/audit/DOCUMENTATION_CLEANUP_PLAN.md` | План cleanup документации | 88 | implemented |
| `docs/implementation/IMPLEMENTATION_PACKAGE.md` | Пакет реализации Phase 1A | 242 | implemented |
| `docs/implementation/PHASE_1A_PROGRESS_REPORT.md` | Progress report, не кодовый аудит | 130 | partial |
| `docs/implementation/PHASE_1A_TASK_PLAN.md` | Детальный task plan | 286 | implemented |
| `scripts/generate_tool_catalog.py` | Future tool catalog generator | 9 | stub |
| `scripts/validate_config.py` | CLI validation для config | 22 | implemented |
| `src/mcp_proxmox/__init__.py` | Version export | 2 | implemented |
| `src/mcp_proxmox/__main__.py` | Entry point bootstrap message | 11 | stub |
| `src/mcp_proxmox/audit/__init__.py` | Audit package marker | 1 | skeleton |
| `src/mcp_proxmox/cache/__init__.py` | Cache package marker | 1 | skeleton |
| `src/mcp_proxmox/config/__init__.py` | Public config exports | 4 | implemented |
| `src/mcp_proxmox/config/loader.py` | Config loading, env expansion, fallback YAML parser | 96 | implemented |
| `src/mcp_proxmox/config/models.py` | Pydantic config models | 57 | implemented |
| `src/mcp_proxmox/domains/__init__.py` | Domains package marker | 1 | skeleton |
| `src/mcp_proxmox/domains/cluster/__init__.py` | Cluster domain marker | 1 | skeleton |
| `src/mcp_proxmox/domains/containers/__init__.py` | LXC domain marker | 1 | skeleton |
| `src/mcp_proxmox/domains/nodes/__init__.py` | Nodes domain marker | 1 | skeleton |
| `src/mcp_proxmox/domains/vms/__init__.py` | VMs domain marker | 1 | skeleton |
| `src/mcp_proxmox/logging/__init__.py` | Public logging exports | 15 | implemented |
| `src/mcp_proxmox/logging/context.py` | correlation_id contextvar helpers | 20 | implemented |
| `src/mcp_proxmox/logging/setup.py` | stdlib JSON/console logging setup | 99 | implemented |
| `src/mcp_proxmox/mcp/__init__.py` | MCP package marker | 1 | skeleton |
| `src/mcp_proxmox/mcp/handlers/__init__.py` | MCP handlers marker | 1 | skeleton |
| `src/mcp_proxmox/mcp/registry/__init__.py` | MCP registry marker | 1 | skeleton |
| `src/mcp_proxmox/mcp/session/__init__.py` | MCP session marker | 1 | skeleton |
| `src/mcp_proxmox/mcp/transport/__init__.py` | MCP transport marker | 1 | skeleton |
| `src/mcp_proxmox/orchestrator/__init__.py` | Orchestrator package marker | 1 | skeleton |
| `src/mcp_proxmox/policy/__init__.py` | Public policy exports | 3 | implemented |
| `src/mcp_proxmox/policy/engine.py` | Policy engine | 31 | implemented |
| `src/mcp_proxmox/pve/__init__.py` | PVE package marker | 1 | skeleton |
| `src/mcp_proxmox/pve/auth/__init__.py` | PVE auth marker | 1 | skeleton |
| `src/mcp_proxmox/pve/client/__init__.py` | PVE client marker | 1 | skeleton |
| `src/mcp_proxmox/pve/models/__init__.py` | PVE models marker | 1 | skeleton |
| `tests/README.md` | Test running notes | 11 | partial |
| `tests/test_skeleton.py` | Version smoke test | 3 | implemented |
| `tests/unit/test_config.py` | Config unit tests | 116 | implemented |
| `tests/unit/test_logging.py` | Logging unit tests | 29 | implemented |
| `tests/unit/test_policy.py` | Policy unit tests | 18 | implemented |
| `tests/unit/__init__.py` | Unit test package marker | 0 | empty |
| `tests/unit/.gitkeep` | Unit test dir placeholder | 0 | placeholder |
| `tests/contract/__init__.py` | Contract test package marker | 0 | empty |
| `tests/contract/fixtures/.gitkeep` | Contract fixtures placeholder | 0 | placeholder |
| `tests/contract/snapshots/.gitkeep` | Contract snapshots placeholder | 0 | placeholder |
| `tests/integration/__init__.py` | Integration test package marker | 0 | empty |
| `tests/integration/mock_pve/.gitkeep` | Mock PVE placeholder | 0 | placeholder |

---

## 3. Module Audit

### 3.1 Config

Files:

- `src/mcp_proxmox/config/__init__.py`
- `src/mcp_proxmox/config/loader.py`
- `src/mcp_proxmox/config/models.py`
- `config/default.yaml`
- `config/schema/config.schema.json`
- `scripts/validate_config.py`

Implemented:

- Strict Pydantic config models with `extra="forbid"`.
- `READ_ONLY` policy mode enum.
- Logging level/format enums.
- Connection, policy, orchestrator, cache, logging, audit, subsystem config models.
- `load_config(path)` loads YAML file and validates it.
- `parse_config(data)` validates in-memory mapping.
- `expand_env(value)` recursively expands `${VAR}` placeholders.
- CLI validator returns `0` for valid config and `1` for invalid config.

Classes:

- `StrictModel`
- `PolicyMode`
- `LogFormat`
- `LogLevel`
- `ConnectionConfig`
- `MemoryPolicyConfig`
- `PolicyConfig`
- `OrchestratorConfig`
- `CacheConfig`
- `LoggingConfig`
- `AuditConfig`
- `LogsSubsystemConfig`
- `SubsystemsConfig`
- `AppConfig`
- `ConfigError`

Functions:

- `load_config`
- `parse_config`
- `expand_env`
- `_replace_env`
- `_load_yaml_file`
- `_parse_simple_yaml`
- `_parse_scalar`
- `scripts.validate_config.main`

Dependencies used:

- stdlib: `os`, `re`, `pathlib`, `argparse`, `sys`
- Pydantic: `BaseModel`, `ConfigDict`, `Field`, `HttpUrl`, `PositiveInt`, `ValidationError`
- Optional runtime dependency: `yaml` from PyYAML, with fallback parser if unavailable.

Missing:

- No merge of `config/default.yaml` + `config/local.yaml`.
- No environment variable prefix mapping such as `MCP_PROXMOX_*`.
- JSON Schema file is not used by `scripts/validate_config.py`.
- Fallback YAML parser is intentionally narrow and not a general YAML implementation.
- No path normalization for audit/data paths.
- No tests for JSON Schema parity.

Status: `implemented` for bootstrap needs, `partial` against full T-100 package intent.

### 3.2 Logging

Files:

- `src/mcp_proxmox/logging/__init__.py`
- `src/mcp_proxmox/logging/context.py`
- `src/mcp_proxmox/logging/setup.py`

Implemented:

- Context-local `correlation_id` using `ContextVar`.
- Context manager for temporary correlation binding.
- JSON-lines formatter.
- Console formatter.
- Root logging configuration.
- Secret redaction by key name for token/secret/password/authorization.

Classes:

- `JsonFormatter`
- `ConsoleFormatter`

Functions:

- `get_correlation_id`
- `set_correlation_id`
- `correlation_context`
- `configure_logging`
- `get_logger`
- `redact`
- `_extra_fields`
- `_is_sensitive_key`
- `_enum_value`

Dependencies used:

- stdlib: `logging`, `json`, `sys`, `contextvars`, `contextlib`
- Internal: `LoggingConfig`, `LogFormat`, `LogLevel`

Missing:

- `structlog` is declared in `pyproject.toml` but not actually used.
- No MCP middleware hook yet.
- No request duration fields.
- No standard event schema beyond formatter output.
- No PVE request correlation fields yet.
- No tests for console formatter.

Status: `implemented` for local structured logging foundation, `partial` against architecture wording that mentions `structlog`.

### 3.3 Policy

Files:

- `src/mcp_proxmox/policy/__init__.py`
- `src/mcp_proxmox/policy/engine.py`

Implemented:

- Tool tiers: `READ`, `OPERATOR`, `ADMIN`.
- `ToolPolicy` dataclass.
- `PolicyEngine.authorize`.
- `READ_ONLY` allows `READ`, denies `OPERATOR` and `ADMIN`.

Classes:

- `ToolTier`
- `PolicyDenied`
- `ToolPolicy`
- `PolicyEngine`

Functions/methods:

- `PolicyEngine.__init__`
- `PolicyEngine.mode`
- `PolicyEngine.authorize`

Dependencies used:

- stdlib: `dataclasses`, `enum`
- Internal: `PolicyConfig`, `PolicyMode`

Missing:

- No registry integration.
- No MCP handler integration.
- No audit events for denied calls.
- No configurable modes beyond `READ_ONLY`.
- No per-tool metadata source yet.

Status: `implemented` for T-103 minimum.

### 3.4 PVE

Files:

- `src/mcp_proxmox/pve/__init__.py`
- `src/mcp_proxmox/pve/auth/__init__.py`
- `src/mcp_proxmox/pve/client/__init__.py`
- `src/mcp_proxmox/pve/models/__init__.py`

Implemented:

- Package structure only.

Classes:

- None.

Functions:

- None.

Dependencies used:

- None in code.
- Planned dependencies in `pyproject.toml`: `httpx`, Pydantic.

Missing:

- No auth header builder.
- No async HTTP client.
- No retry/TLS handling.
- No `PveApiError`.
- No PVE DTO models.
- No unit tests.

Status: `skeleton`.

### 3.5 MCP

Files:

- `src/mcp_proxmox/mcp/__init__.py`
- `src/mcp_proxmox/mcp/handlers/__init__.py`
- `src/mcp_proxmox/mcp/registry/__init__.py`
- `src/mcp_proxmox/mcp/session/__init__.py`
- `src/mcp_proxmox/mcp/transport/__init__.py`
- `src/mcp_proxmox/__main__.py`

Implemented:

- Package structure.
- Entry point exists but only prints bootstrap message.

Classes:

- None.

Functions:

- `mcp_proxmox.__main__.main`

Dependencies used:

- None in MCP package.
- Planned dependency in `pyproject.toml`: `mcp`.

Missing:

- No MCP SDK usage.
- No stdio server.
- No tool registry.
- No handlers.
- No list_tools response.
- No session context.
- No graceful shutdown.

Status: `skeleton` for packages, `stub` for entrypoint.

### 3.6 Orchestrator

Files:

- `src/mcp_proxmox/orchestrator/__init__.py`

Implemented:

- Package marker only.

Classes:

- None.

Functions:

- None.

Dependencies used:

- None.

Missing:

- Node discovery.
- Fan-out.
- Semaphores/limits.
- Pagination helpers.
- Partial results/errors model.
- Tests.

Status: `skeleton`.

### 3.7 Domains

Files:

- `src/mcp_proxmox/domains/__init__.py`
- `src/mcp_proxmox/domains/cluster/__init__.py`
- `src/mcp_proxmox/domains/containers/__init__.py`
- `src/mcp_proxmox/domains/nodes/__init__.py`
- `src/mcp_proxmox/domains/vms/__init__.py`

Implemented:

- Package structure for Phase 1A domains.

Classes:

- None.

Functions:

- None.

Dependencies used:

- None.

Missing:

- No Cluster domain tools.
- No Node domain tools.
- No LXC domain tools.
- No QEMU VM domain tools.
- No DTOs.
- No contract tests.

Status: `skeleton`.

### 3.8 Audit

Files:

- `src/mcp_proxmox/audit/__init__.py`

Implemented:

- Package marker only.

Classes:

- None.

Functions:

- None.

Dependencies used:

- None.

Missing:

- No JSON-lines writer.
- No append-only audit events.
- No path handling from config.
- No tool-call integration.
- No tests.

Status: `skeleton`.

### 3.9 Cache

Files:

- `src/mcp_proxmox/cache/__init__.py`

Implemented:

- Package marker only.

Classes:

- None.

Functions:

- None.

Dependencies used:

- None.

Missing:

- No TTL cache.
- No per-tool cache policy.
- No invalidation.
- No tests.

Status: `skeleton`.

---

## 4. Closed/Claimed Task Audit

### T-004 — Repository Skeleton

Created files:

- `README.md`
- `CHANGELOG.md`
- `LICENSE`
- `.env.example`
- `.gitignore`
- `pyproject.toml`
- `config/default.yaml`
- `config/schema/config.schema.json`
- `deploy/Dockerfile`
- `deploy/docker-compose.yml`
- `deploy/mcp-client.example.json`
- `scripts/validate_config.py`
- `scripts/generate_tool_catalog.py`
- `src/mcp_proxmox/**`
- `tests/**`
- `data/.gitkeep`

Modified files:

- `docs/implementation/PHASE_1A_TASK_PLAN.md`
- `docs/adr/0001-implementation-language.md`
- `docs/adr/0002-mcp-transport.md`
- `docs/adr/ADR_INDEX.md`

DoD actually completed:

- Repository tree mostly exists.
- `pyproject.toml` exists.
- `LICENSE` exists.
- README stub exists.
- Empty package structure exists.
- Local test/lint command configuration exists in `pyproject.toml`.

DoD partial/not completed:

- `pip install -e ".[dev]"` not verified.
- `pytest` not verified because pytest is not installed in available Python.
- `ruff` not verified.
- `mypy` not verified.
- No CI by design, because project is local and not GitHub-hosted.

Audit status: `partial`, not fully closed by strict DoD.

### T-100 — Config Loader + Schema Validation

Created files:

- `src/mcp_proxmox/config/models.py`
- `src/mcp_proxmox/config/loader.py`
- `tests/unit/test_config.py`

Modified files:

- `src/mcp_proxmox/config/__init__.py`
- `scripts/validate_config.py`
- `tests/README.md`
- `docs/implementation/PHASE_1A_TASK_PLAN.md`
- `docs/implementation/PHASE_1A_PROGRESS_REPORT.md`
- `CHANGELOG.md`

DoD actually completed:

- Invalid config returns non-zero from `scripts/validate_config.py`.
- Secrets are required through env placeholders in `config/default.yaml`.
- Unit tests exist and pass under `unittest`.
- Pydantic validation exists.

DoD partial/not completed:

- JSON Schema exists but is not used by runtime validator.
- `config/local.yaml` merge not implemented.
- Full env override model not implemented.
- PyYAML declared but not available in current bootstrap Python; fallback parser is narrow.

Audit status: `implemented` for current code, `partial` against full package expectations.

### T-101 — Structured Logging + Correlation ID

Created files:

- `src/mcp_proxmox/logging/context.py`
- `src/mcp_proxmox/logging/setup.py`
- `tests/unit/test_logging.py`

Modified files:

- `src/mcp_proxmox/logging/__init__.py`
- `docs/implementation/PHASE_1A_TASK_PLAN.md`
- `docs/implementation/PHASE_1A_PROGRESS_REPORT.md`
- `CHANGELOG.md`

DoD actually completed:

- JSON log contains `correlation_id`.
- Token/secret-like fields are redacted.
- Unit tests exist and pass.

DoD partial/not completed:

- `structlog` not used.
- No MCP middleware hook because MCP server does not exist yet.
- No integration with PVE client or handlers.

Audit status: `implemented` for isolated logging helpers, `partial` as subsystem.

### T-103 — Policy Engine

Created files:

- `src/mcp_proxmox/policy/engine.py`
- `tests/unit/test_policy.py`

Modified files:

- `src/mcp_proxmox/policy/__init__.py`
- `docs/implementation/PHASE_1A_TASK_PLAN.md`
- `docs/implementation/PHASE_1A_PROGRESS_REPORT.md`
- `CHANGELOG.md`

DoD actually completed:

- Unit tests: `READ` allowed.
- Unit tests: `OPERATOR` denied.
- Unit tests: `ADMIN` denied.
- Engine uses `PolicyConfig.mode`.

DoD partial/not completed:

- No registry integration.
- No tool handler integration.
- No audit integration.

Audit status: `implemented` for isolated policy engine.

---

## 5. Stub / Placeholder Inventory

| File | Type | Purpose | Related task |
|------|------|---------|--------------|
| `src/mcp_proxmox/__main__.py` | stub | Prints `MCP stdio server is planned for T-104`; does not start MCP | T-104 |
| `scripts/generate_tool_catalog.py` | stub | Prints catalog generation planned for T-211 | T-211 |
| `src/mcp_proxmox/audit/__init__.py` | skeleton | Audit package marker only | T-112 |
| `src/mcp_proxmox/cache/__init__.py` | skeleton | Cache package marker only | T-210 / optional Phase 1A cache |
| `src/mcp_proxmox/mcp/**/__init__.py` | skeleton | MCP package/handlers/registry/session/transport markers | T-104, T-105, T-111 |
| `src/mcp_proxmox/pve/**/__init__.py` | skeleton | PVE package/auth/client/models markers | T-102 |
| `src/mcp_proxmox/orchestrator/__init__.py` | skeleton | Orchestrator package marker | T-106 |
| `src/mcp_proxmox/domains/**/__init__.py` | skeleton | Domain package markers for cluster/nodes/LXC/VM | T-107...T-110 |
| `tests/contract/fixtures/.gitkeep` | placeholder | Future contract fixtures | T-114 |
| `tests/contract/snapshots/.gitkeep` | placeholder | Future snapshots | T-114 |
| `tests/integration/mock_pve/.gitkeep` | placeholder | Future mock PVE fixture | T-005 |
| `data/.gitkeep` | placeholder | Future runtime data/audit storage | T-112 / Phase 2 |
| `docs/adr/template.md` | placeholder/template | Future ADR creation | future ADRs |

Search results:

- No `NotImplementedError` found.
- No code-level `pass` found.
- No `TODO` found in Python source.
- Explicit planned/stub strings found in `__main__.py` and `generate_tool_catalog.py`.

---

## 6. Test Coverage Audit

Existing tests:

| Test file | Tests | What it checks |
|-----------|-------|----------------|
| `tests/test_skeleton.py` | 1 | Package version is defined |
| `tests/unit/test_config.py` | 6 | Valid config parsing, invalid policy mode, extra keys rejection, env expansion, missing env error, YAML file loading |
| `tests/unit/test_logging.py` | 3 | JSON log includes correlation id, token redaction, nested redaction |
| `tests/unit/test_policy.py` | 3 | READ allowed, OPERATOR denied, ADMIN denied |

Total tests discovered by stdlib unittest: **12**.

Command executed:

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -p "test_*.py"
```

Observed result:

```text
Ran 12 tests in 0.013s
OK
```

Modules covered:

- `mcp_proxmox.config`
- `mcp_proxmox.logging`
- `mcp_proxmox.policy`
- package version export

Modules not covered:

- `mcp_proxmox.__main__`
- `mcp_proxmox.pve`
- `mcp_proxmox.mcp`
- `mcp_proxmox.orchestrator`
- `mcp_proxmox.domains`
- `mcp_proxmox.audit`
- `mcp_proxmox.cache`
- `scripts.validate_config.py` subprocess behavior is manually checked, not unit-tested.
- `scripts.generate_tool_catalog.py`

Unavailable checks in current environment:

- `pytest`: not installed.
- `ruff`: not installed.
- `mypy`: not installed.
- `pip install -e ".[dev]"`: not verified.

---

## 7. Run/Entrypoint Audit

Entrypoint exists:

- `pyproject.toml`: `mcp-proxmox = "mcp_proxmox.__main__:main"`
- Module entrypoint: `python -m mcp_proxmox`

Observed run:

```text
mcp-proxmox bootstrap: MCP stdio server is planned for T-104.
```

Can the project be considered runnable?

- Yes, in the narrow sense: Python module entrypoint executes and exits successfully.
- No, in product/MCP sense: it does not start an MCP server, register tools, read config, or connect to Proxmox.

Current launch status: `stub`.

---

## 8. Readiness Table

| Component | Readiness | Comment |
|-----------|-----------|---------|
| Config System | 65% | Working Pydantic loader + CLI validator; lacks config layering/env override/schema integration |
| Logging | 45% | Working stdlib JSON/console + correlation/redaction; no MCP/PVE integration, no structlog |
| Policy Engine | 55% | Core READ_ONLY logic works; not wired to registry/handlers |
| MCP Server | 5% | Package structure and entrypoint only; no MCP SDK server |
| PVE Client | 0% | No client/auth/errors/models |
| Orchestrator | 0% | Package marker only |
| Domains | 0% | Package markers only |
| Audit | 0% | Package marker only |
| Cache | 0% | Package marker only |
| Tests | 25% | 12 unit tests for implemented islands; no pytest/contract/integration/mock PVE |
| Deploy | 15% | Docker/compose sketches exist; not build-tested and entrypoint is stub |
| Documentation | 80% | Architecture/roadmap/ADR base is strong; some docs now ahead of code |

---

## 9. Honest Current-State Estimate

This estimate is based on actual code, not roadmap status.

- Architecture/documentation readiness: **~75-80%** for Phase 1A planning.
- Codebase readiness for Phase 1A MVP: **~15-20%**.
- Runtime readiness as an MCP server: **~5%**.
- Proxmox integration readiness: **0%**.
- Test maturity: **~20-25%** for implemented code, **<10%** for Phase 1A as a whole.

Approximate tasks remaining before first working MCP:

1. Implement T-104 minimal MCP stdio server and registry.
2. Implement T-105 session/correlation context wiring.
3. Implement at least a fake or static first READ tool to prove MCP call path.
4. Implement T-102 PVE client.
5. Implement at least T-107/T-108 minimal cluster/nodes tools.

Approximate tasks remaining before useful Phase 1A MVP:

1. T-104 MCP stdio server.
2. T-105 session context.
3. T-102 PVE HTTP client.
4. T-106 orchestrator basics.
5. T-107 cluster domain.
6. T-108 node domain.
7. T-109 LXC domain.
8. T-110 VM domain.
9. T-111 handler wire-up for 8 tools.
10. T-005/T-114/T-115 testing support.

Bottom line:

The repository has a good architectural foundation and a small amount of real bootstrap code. It is not yet a working MCP server. The most valuable next technical milestone is not more scaffolding, but a minimal T-104 MCP stdio server wired to the existing config/logging/policy pieces.
