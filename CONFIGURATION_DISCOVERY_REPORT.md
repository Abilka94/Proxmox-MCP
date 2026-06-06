# Configuration Discovery Report

**Date:** 2026-06-06
**Status:** Analysis complete (no code changes)

---

## 1. How Configuration Is Loaded

### Entry Point

`src/mcp_proxmox/__main__.py:22` — `config = load_config()`

Called from `main()` which is invoked via the `mcp-proxmox` console script (defined in `pyproject.toml`).

### Config Loader

`src/mcp_proxmox/config/loader.py` implements a 3-stage pipeline:

```
load_config(path?)                   # Stage 1: resolve config path
  → _load_yaml_file(path) → dict    # Stage 2: read + parse YAML (pyyaml or fallback)
  → expand_env(dict) → dict          # Stage 3: replace ${VAR} placeholders with os.environ
  → parse_config(dict) → AppConfig   # Stage 4: Pydantic model_validate
```

- Default config path: `config/default.yaml` (relative to CWD)
- Override via `MCP_PROXMOX_CONFIG` env var or explicit `path` argument to `load_config()`
- Missing env vars referenced in YAML raise `ConfigError`

### Pydantic Models

All in `src/mcp_proxmox/config/models.py`:

| Model | Required | Key Fields |
|-------|----------|------------|
| `AppConfig` | Yes | `connection`, `policy` (required); `orchestrator`, `cache`, `logging`, `audit`, `subsystems` (optional, have defaults) |
| `ConnectionConfig` | Yes | `id`, `host` (HttpUrl), `token_id`, `token_secret` (all min_length=1), `verify_ssl` (default True) |
| `PolicyConfig` | Yes | `mode` (default READ_ONLY), `memory` |
| `OrchestratorConfig` | No | `max_concurrent_per_node`, `max_concurrent_cluster`, `node_request_timeout_sec`, `aggregate_threshold` |
| `CacheConfig` | No | `cluster_resources_ttl_sec`, `node_status_ttl_sec` |
| `LoggingConfig` | No | `level` (INFO), `format` (console) |
| `AuditConfig` | No | `path` |
| `SubsystemsConfig` | No | `logs` |

All models use `extra="forbid"` — unknown keys are rejected at validation time.

### Sources of Configuration

| Source | Supported? | Details |
|--------|-----------|---------|
| YAML file | **Yes** | `config/default.yaml` by default; override via `MCP_PROXMOX_CONFIG` env var |
| Environment variables within YAML | **Yes** | `${PVE_HOST}`, `${PVE_TOKEN_ID}`, `${PVE_TOKEN_SECRET}` placeholders expanded after YAML parse |
| Direct env var overrides | **No** | Not supported |
| `.env` file | **No** | Not loaded by Python code (Docker compose uses `env_file`, but that's external) |
| CLI arguments | **No** | Not supported |

---

## 2. Supported Mechanisms

| Mechanism | Supported? | Evidence |
|-----------|-----------|----------|
| `.env` file | **No** | No python-dotenv dependency. No `load_dotenv()` call anywhere. Grep returned zero results for `dotenv\|python-dotenv\|load_dotenv`. |
| `python-dotenv` | **No** | Not in `pyproject.toml` dependencies. Not imported anywhere. |
| Environment variables | **Partial** | Only as `${VAR}` placeholders inside YAML values. No direct env-var-to-config-key mapping. |
| YAML config | **Yes** | Main mechanism. `pyyaml>=6.0,<7` is a dependency. Falls back to hand-written `_parse_simple_yaml()` if pyyaml is unavailable. |
| `pydantic-settings` | **No** (`pyproject.toml` dependency but unused) | Listed in dependencies (`pydantic-settings>=2.3,<3`) but never imported or used anywhere in the codebase. Would provide `BaseSettings` for env-var-driven config. |

**Conclusion**: The current system uses a **YAML-centric** approach with environment variable substitution. There is no `.env` loading, no `pydantic-settings` usage, and no CLI argument support.

---

## 3. Parameter Resolution

| Parameter | Where It's Read From | Mechanism Implemented |
|-----------|---------------------|-----------------------|
| **base_url** | `config/default.yaml` → `connection.host` = `${PVE_HOST}` | Env var `${PVE_HOST}` expanded into YAML value; validated as `pydantic.HttpUrl` |
| **token_id** | `config/default.yaml` → `connection.token_id` = `${PVE_TOKEN_ID}` | Env var `${PVE_TOKEN_ID}` expanded into YAML value; validated as `str(min_length=1)` |
| **token_secret** | `config/default.yaml` → `connection.token_secret` = `${PVE_TOKEN_SECRET}` | Env var `${PVE_TOKEN_SECRET}` expanded into YAML value; validated as `str(min_length=1)` |
| **verify_ssl** | `config/default.yaml` → `connection.verify_ssl` = `true` | Hardcoded literal in YAML (not env-driven); validated as `bool` |
| **timeout** | `config/default.yaml` → `orchestrator.node_request_timeout_sec` = `30` | Hardcoded literal in YAML (not env-driven); validated as `PositiveInt` |

`verify_ssl` and `timeout` **could** be made env-driven (`${PVE_VERIFY_SSL}`, `${PVE_TIMEOUT}`) by simply changing `config/default.yaml`, but currently they are static.

The resolved values are consumed via `src/mcp_proxmox/pve/auth/config.py:auth_config_from_app_config()` which builds a `PveAuthConfig` dataclass:

```python
PveAuthConfig(
    base_url=str(config.connection.host).rstrip("/"),
    token_id=config.connection.token_id,
    token_secret=config.connection.token_secret,
    verify_ssl=config.connection.verify_ssl,
    timeout_sec=float(config.orchestrator.node_request_timeout_sec),
)
```

The `PveAuthConfig.authorization_header` property constructs the HTTP auth header: `PVEAPIToken={token_id}={token_secret}`.

---

## 4. Recommended Secret Storage

Given the current architecture (YAML + env var substitution), the recommended approach is:

| Storage | Risk Level | Recommendation |
|---------|-----------|---------------|
| **System environment variables** (export in shell profile, systemd unit, Docker env) | **Lowest** | **Recommended for production.** Secrets never written to disk. Docker compose already supports `env_file: ../.env`. |
| **`.env` file** (outside repo, listed in `.gitignore`) | **Low** | Good for local dev. Already in `.gitignore` (line 14: `.env`). Python does NOT load it automatically — user must source it or use Docker.|
| **`config/local.yaml`** (outside version control, listed in `.gitignore`) | **Low** | Already in `.gitignore` (line 15: `config/local.yaml`). User can create a copy of `default.yaml` with hardcoded values. |
| **`config/default.yaml` with hardcoded secrets** | **High** | **Never do this.** Not in `.gitignore` — secrets will be committed to git. |

### What `.gitignore` Covers

```
.env                         # ignored — safe for local secrets
config/local.yaml             # ignored — safe for local overrides
data/*                        # ignored — audit logs, cached data
__pycache__/, *.pyc, etc.     # ignored
```

`config/default.yaml` is **NOT** in `.gitignore` — it is tracked by git.

### Recommendation for Local Development

```
1. Copy .env.example → .env
2. Fill in real secrets in .env
3. Run with Docker (reads .env automatically) or source .env in shell
```

### Recommendation for Production

```
1. Set PVE_HOST, PVE_TOKEN_ID, PVE_TOKEN_SECRET via systemd environment,
   Kubernetes secrets, or Docker env_file (pointing to a secure .env outside the repo)
2. Keep config/default.yaml as-is (uses ${VAR} placeholders)
3. Never write secrets to tracked files
```

---

## 5. Secret Leak Assessment

### 5.1 Will secrets leak to git?

| File | Tracked? | Risk |
|------|----------|------|
| `config/default.yaml` | **Yes** (tracked) | **No risk** — uses `${PVE_TOKEN_ID}` / `${PVE_TOKEN_SECRET}` placeholders, not actual secrets |
| `.env` | **No** (in `.gitignore`) | **No risk** — ignored by git |
| `config/local.yaml` | **No** (in `.gitignore`) | **No risk** — ignored by git |
| Code files | **Yes** (tracked) | **No risk** — no secrets hardcoded in source |

**Verdict: No git leak risk with current placeholder-based approach.**

### 5.2 Will secrets leak to logs?

| Log Format | Redaction Mechanism | Risk |
|-----------|-------------------|------|
| **JSON** (logging.format: json) | `JsonFormatter` → `redact()` function in `src/mcp_proxmox/logging/setup.py` | **Protected.** Recursively walks logged dicts and replaces any key containing `token`, `secret`, `password`, or `authorization` with `[REDACTED]`. |
| **Console** (logging.format: console) | No redaction (just outputs `level [correlation_id] logger: message`) | **Low risk.** Structured extra fields (where secrets would appear) are not rendered by `ConsoleFormatter`. However, if any log message string itself contains a secret, it would not be redacted. |

**Caveat**: `token_id` is redacted from structured log extras due to the "token" key substring, but it may be desirable to see `token_id` in operational logs (it is not a secret — only `token_secret` is). The current redaction is aggressive and redacts `token_id` too. This is acceptable for now.

**Verdict: Low risk. Secrets in structured fields are redacted. Message strings should not contain secrets.**

### 5.3 Will secrets leak to reports?

| Report | Details | Risk |
|--------|---------|------|
| Audit logs (`data/audit.log`) | Write path is `data/` which is in `.gitignore`. Audit module exists as a stub/config only — no audit writing code is implemented yet. | **No current risk.** When implemented, use same redaction. |
| `INFRASTRUCTURE_READ_COMPLETION_REPORT.md` and other `.md` reports | Generated by AI, not by the application. | **No risk** — manually written by tool, no code path exposes secrets. |
| Error/diagnostic output | `ConfigError` messages may reference env var names but not values. | **No risk.** |

**Verdict: No report leak risk in current implementation.**

---

## 6. Example Safe Configuration for Validation Sprint

### 6.1 `.env` (local dev, excluded from git)

```bash
# .env — copy from .env.example, fill with test values
PVE_HOST=https://pve.example.local:8006
PVE_TOKEN_ID=root@pam!mcp-proxmox
PVE_TOKEN_SECRET=replace-me
MCP_PROXMOX_CONFIG=config/default.yaml
```

### 6.2 `config/local.yaml` (local override, excluded from git)

```yaml
# config/local.yaml — hardcoded for validation, excluded from git
connection:
  id: "validation-cluster"
  host: "https://pve.validation.local:8006"
  token_id: "root@pam!validation-token"
  token_secret: "validation-secret-placeholder"
  verify_ssl: false

policy:
  mode: READ_ONLY
  memory:
    allow_write: false

logging:
  level: DEBUG
  format: json

orchestrator:
  node_request_timeout_sec: 60
```

Use with: `MCP_PROXMOX_CONFIG=config/local.yaml mcp-proxmox`

### 6.3 Production `config/default.yaml` (unchanged, tracked)

```yaml
connection:
  id: "local"
  host: "${PVE_HOST}"
  token_id: "${PVE_TOKEN_ID}"
  token_secret: "${PVE_TOKEN_SECRET}"
  verify_ssl: true

policy:
  mode: READ_ONLY
  memory:
    allow_write: true

orchestrator:
  max_concurrent_per_node: 5
  max_concurrent_cluster: 15
  node_request_timeout_sec: 30
  aggregate_threshold: 500

cache:
  cluster_resources_ttl_sec: 30
  node_status_ttl_sec: 15

logging:
  level: INFO
  format: console

audit:
  path: "data/audit.log"

subsystems:
  logs:
    enabled: true
    max_lines: 500
```

---

## Summary

| Aspect | Status |
|--------|--------|
| Config source | YAML file with env var substitution |
| `.env` support | **Not implemented** in Python (Docker handles externally) |
| `python-dotenv` | **Not used** |
| `pydantic-settings` | Dependency present but **unused** |
| Secrets in git | **Safe** — placeholders only in tracked files, actual secrets in `.gitignore`-protected files |
| Secrets in logs | **Redacted** — JSON formatter replaces `token`/`secret` keys with `[REDACTED]` |
| Secrets in reports | **No risk** — no code path writes secrets to reports |
| `verify_ssl` / `timeout` | Static values in YAML, not env-driven |
| Recommended storage | System env vars (production), `.env` + Docker (local dev), `config/local.yaml` (validation sprint) |
