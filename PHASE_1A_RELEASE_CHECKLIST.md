# Phase 1A Release Checklist

**Date:** 2026-06-06

---

## Pre-Commit Verification

| Check | Status | Notes |
|-------|--------|-------|
| Secrets in tracked files | ✅ PASS | No secrets found. `config/local.yaml` uses placeholders or is untracked. |
| Tokens in source code | ✅ PASS | No tokens hardcoded. Token flows via `os.environ` / YAML config. |
| `config/local.yaml` in git index | ✅ PASS | Not tracked. Confirmed via `git check-ignore`. |
| `.env` in git index | ✅ PASS | Not tracked. Listed in `.gitignore`. |
| Temp files removed | ✅ PASS | `config/Текстовый документ.txt` deleted. |
| `__pycache__` in git index | ✅ PASS | Listed in `.gitignore` — ignored. |
| Validation artifacts | ✅ PASS | `scripts/test_live_connection.py` and `scripts/validate_live_mcp.py` are intentional committed artifacts. |
| `config/local.yaml` hardcoded secrets | ⚠️ OK | File is ignored by git. Will not be committed. |

---

## Git Status Summary

| Category | Count | Details |
|----------|-------|---------|
| Modified (tracked) | 19 | Source code, tests, INFRASTRUCTURE_READ_COMPLETION_REPORT.md |
| New (untracked, to commit) | 7 | Closure documents + validation scripts |
| New (untracked, temp) | 0 | Cleaned |
| Ignored | — | `__pycache__/`, `.env`, `config/local.yaml`, `data/*`, `*.pyc` |

---

## Files to Commit

### Source code (19 modified files)

```
src/mcp_proxmox/domains/containers/__init__.py
src/mcp_proxmox/domains/containers/service.py
src/mcp_proxmox/domains/storage/__init__.py
src/mcp_proxmox/domains/storage/service.py
src/mcp_proxmox/domains/updates/__init__.py
src/mcp_proxmox/domains/updates/service.py
src/mcp_proxmox/domains/vms/__init__.py
src/mcp_proxmox/domains/vms/service.py
src/mcp_proxmox/mcp/registry/tools.py
src/mcp_proxmox/pve/client/core.py
src/mcp_proxmox/pve/models/__init__.py
src/mcp_proxmox/pve/models/responses.py
tests/unit/test_domain_containers.py
tests/unit/test_domain_storage.py
tests/unit/test_domain_updates.py
tests/unit/test_domain_vms.py
tests/unit/test_mcp_server.py
tests/unit/test_pve_client.py
INFRASTRUCTURE_READ_COMPLETION_REPORT.md
```

### New files (7 files)

```
CONFIGURATION_DISCOVERY_REPORT.md
LIVE_CLUSTER_CONFIGURATION_GUIDE.md
LIVE_MCP_VALIDATION_REPORT.md
LIVE_VALIDATION_EXECUTION_PLAN.md
VALIDATION_REMEDIATION_REPORT.md
scripts/test_live_connection.py
scripts/validate_live_mcp.py
PHASE_1A_ACCEPTANCE.md
```

### Final new files for this closure

```
PHASE_1A_ACCEPTANCE.md
PHASE_1A_RELEASE_CHECKLIST.md
RELEASE_NOTES_v0.1.0-phase1a.md
```

---

## Commit and Tag Checklist

- [ ] All 91 unit tests pass
- [ ] Live validation completed and documented
- [ ] Validation remediation applied and verified
- [ ] No secrets or tokens in tracked files
- [ ] No temp files in working tree
- [ ] Commit message ready
- [ ] Tag ready
- [ ] Release notes ready
