# Documentation Restructure Plan

**Date:** 2026-06-06
**Status:** Proposed — pending execution

---

## 1. Current State

### Root-level `.md` files (21 files)

| File | Phase | Target Directory |
|------|-------|-----------------|
| `PHASE_1A_ACCEPTANCE.md` | 1A | `docs/phase-1a/acceptance/` |
| `PHASE_1A_RELEASE_CHECKLIST.md` | 1A | `docs/phase-1a/reports/` |
| `INFRASTRUCTURE_READ_COMPLETION_REPORT.md` | 1A | `docs/phase-1a/reports/` |
| `DOMAIN_READ_TOOLS_REPORT.md` | 1A | `docs/phase-1a/reports/` |
| `T102_IMPLEMENTATION_REPORT.md` | 1A | `docs/phase-1a/reports/` |
| `T104_IMPLEMENTATION_REPORT.md` | 1A | `docs/phase-1a/reports/` |
| `TECHNICAL_DEBT_REMEDIATION_REPORT.md` | 1A | `docs/phase-1a/reports/` |
| `LIVE_CLUSTER_CONFIGURATION_GUIDE.md` | 1A | `docs/phase-1a/validation/` |
| `LIVE_MCP_VALIDATION_REPORT.md` | 1A | `docs/phase-1a/validation/` |
| `LIVE_VALIDATION_EXECUTION_PLAN.md` | 1A | `docs/phase-1a/validation/` |
| `VALIDATION_REMEDIATION_REPORT.md` | 1A | `docs/phase-1a/validation/` |
| `PHASE_1B_TASK_DOMAIN_DESIGN.md` | 1B.1 | `docs/phase-1b/phase-1b.1/design/` |
| `PHASE_1B_IMPLEMENTATION_REPORT.md` | 1B.1 | `docs/phase-1b/phase-1b.1/implementation/` |
| `PHASE_1B_LIVE_VALIDATION_PLAN.md` | 1B.1 | `docs/phase-1b/phase-1b.1/validation/` |
| `PHASE_1B_LIVE_VALIDATION_REPORT.md` | 1B.1 | `docs/phase-1b/phase-1b.1/validation/` |
| `PHASE_1B_VALIDATION_REMEDIATION_REPORT.md` | 1B.1 | `docs/phase-1b/phase-1b.1/validation/` |
| `PHASE_1B_CONNECTIVITY_INVESTIGATION.md` | 1B.1 | `docs/phase-1b/phase-1b.1/validation/` |
| `PHASE_1B_ACCEPTANCE.md` | 1B.1 | `docs/phase-1b/phase-1b.1/acceptance/` |
| `CODEBASE_AUDIT_REPORT.md` | Pre-1A | `docs/archive/` |
| `COMPETITIVE_ANALYSIS.md` | Pre-1A | `docs/archive/` |
| `CONFIGURATION_DISCOVERY_REPORT.md` | Pre-1A | `docs/archive/` |
| `INDEPENDENT_PROJECT_REVIEW.md` | Pre-1A | `docs/archive/reviews/` |
| `RELEASE_NOTES_v0.1.0-phase1a.md` | 1A | `docs/releases/` |

### `docs/` files that need relocation

| Current Path | Target Path |
|-------------|-------------|
| `docs/ARCHITECTURE.md` | `docs/architecture/ARCHITECTURE.md` |
| `docs/IMPLEMENTATION_ROADMAP.md` | `docs/releases/IMPLEMENTATION_ROADMAP.md` |
| `docs/MEMORY_KNOWLEDGE_MODEL.md` | `docs/architecture/MEMORY_KNOWLEDGE_MODEL.md` |
| `docs/implementation/PHASE_1A_TASK_PLAN.md` | `docs/phase-1a/reports/PHASE_1A_TASK_PLAN.md` |
| `docs/implementation/PHASE_1A_PROGRESS_REPORT.md` | `docs/phase-1a/reports/PHASE_1A_PROGRESS_REPORT.md` |
| `docs/implementation/IMPLEMENTATION_PACKAGE.md` | `docs/phase-1a/reports/IMPLEMENTATION_PACKAGE.md` |
| `docs/audit/DOCUMENTATION_AUDIT.md` | `docs/archive/DOCUMENTATION_AUDIT.md` |
| `docs/audit/DOCUMENTATION_CLEANUP_PLAN.md` | `docs/archive/DOCUMENTATION_CLEANUP_PLAN.md` |

### Files that STAY in place

| File | Reason |
|------|--------|
| `README.md` | Root project readme (allowed) |
| `CHANGELOG.md` | Root changelog (allowed) |
| `tests/README.md` | Test documentation (stays with tests/) |
| `docs/adr/*` | Already in correct location |
| `docs/archive/README.md` | Already in archive |
| `docs/archive/recommendations/*` | Already in archive |
| `docs/archive/reviews/ARCHITECTURE_REVIEW_2026-06-03.md` | Already in archive |

---

## 2. Target Directory Structure

```
docs/
├── README.md                      ← entry point (update)
│
├── architecture/
│   ├── ARCHITECTURE.md            ← from docs/ARCHITECTURE.md
│   └── MEMORY_KNOWLEDGE_MODEL.md  ← from docs/MEMORY_KNOWLEDGE_MODEL.md
│
├── adr/                           ← unchanged
│   ├── ADR_INDEX.md
│   ├── template.md
│   ├── 0001-implementation-language.md
│   ├── 0002-mcp-transport.md
│   ├── 0005-ai-proxmox-operator-positioning.md
│   ├── 0006-two-level-knowledge-model.md
│   ├── 0007-entityref.md
│   ├── 0008-pve-compatibility-matrix.md
│   ├── 0009-scalability-limits.md
│   └── 0010-service-type-taxonomy.md
│
├── releases/
│   ├── IMPLEMENTATION_ROADMAP.md   ← from docs/IMPLEMENTATION_ROADMAP.md
│   └── RELEASE_NOTES_v0.1.0-phase1a.md  ← from root
│
├── phase-1a/
│   ├── reports/
│   │   ├── PHASE_1A_TASK_PLAN.md              ← from docs/implementation/
│   │   ├── PHASE_1A_PROGRESS_REPORT.md        ← from docs/implementation/
│   │   ├── IMPLEMENTATION_PACKAGE.md           ← from docs/implementation/
│   │   ├── PHASE_1A_RELEASE_CHECKLIST.md       ← from root
│   │   ├── INFRASTRUCTURE_READ_COMPLETION_REPORT.md  ← from root
│   │   ├── DOMAIN_READ_TOOLS_REPORT.md         ← from root
│   │   ├── T102_IMPLEMENTATION_REPORT.md       ← from root
│   │   ├── T104_IMPLEMENTATION_REPORT.md       ← from root
│   │   └── TECHNICAL_DEBT_REMEDIATION_REPORT.md  ← from root
│   │
│   ├── validation/
│   │   ├── LIVE_CLUSTER_CONFIGURATION_GUIDE.md  ← from root
│   │   ├── LIVE_MCP_VALIDATION_REPORT.md        ← from root
│   │   ├── LIVE_VALIDATION_EXECUTION_PLAN.md    ← from root
│   │   └── VALIDATION_REMEDIATION_REPORT.md     ← from root
│   │
│   └── acceptance/
│       └── PHASE_1A_ACCEPTANCE.md               ← from root
│
├── phase-1b/
│   ├── phase-1b.1/
│   │   ├── design/
│   │   │   └── PHASE_1B_TASK_DOMAIN_DESIGN.md   ← from root
│   │   │
│   │   ├── implementation/
│   │   │   └── PHASE_1B_IMPLEMENTATION_REPORT.md  ← from root
│   │   │
│   │   ├── validation/
│   │   │   ├── PHASE_1B_LIVE_VALIDATION_PLAN.md  ← from root
│   │   │   ├── PHASE_1B_LIVE_VALIDATION_REPORT.md  ← from root
│   │   │   ├── PHASE_1B_VALIDATION_REMEDIATION_REPORT.md  ← from root
│   │   │   └── PHASE_1B_CONNECTIVITY_INVESTIGATION.md  ← from root
│   │   │
│   │   └── acceptance/
│   │       └── PHASE_1B_ACCEPTANCE.md            ← from root
│   │
│   └── phase-1b.2/
│       └── .gitkeep                              ← placeholder for future docs
│
├── phase-1c/
│   └── .gitkeep                                  ← placeholder for future docs
│
└── archive/
    ├── README.md                                 ← unchanged
    ├── CODEBASE_AUDIT_REPORT.md                  ← from root
    ├── COMPETITIVE_ANALYSIS.md                   ← from root
    ├── CONFIGURATION_DISCOVERY_REPORT.md          ← from root
    ├── DOCUMENTATION_AUDIT.md                    ← from docs/audit/
    ├── DOCUMENTATION_CLEANUP_PLAN.md             ← from docs/audit/
    ├── recommendations/
    │   └── ARCHITECTURE_UPDATE_RECOMMENDATIONS.md ← unchanged
    └── reviews/
        ├── ARCHITECTURE_REVIEW_2026-06-03.md      ← unchanged
        └── INDEPENDENT_PROJECT_REVIEW.md          ← from root
```

---

## 3. Files That Require Internal Link Updates

| File | Old Link | New Link |
|------|----------|----------|
| `README.md` | `docs/ARCHITECTURE.md` | `docs/architecture/ARCHITECTURE.md` |
| `README.md` | `docs/implementation/IMPLEMENTATION_PACKAGE.md` | `docs/phase-1a/reports/IMPLEMENTATION_PACKAGE.md` |
| `README.md` | `docs/implementation/PHASE_1A_TASK_PLAN.md` | `docs/phase-1a/reports/PHASE_1A_TASK_PLAN.md` |
| `docs/ARCHITECTURE.md` → `docs/architecture/ARCHITECTURE.md` | `MEMORY_KNOWLEDGE_MODEL.md` | `MEMORY_KNOWLEDGE_MODEL.md` (same dir: `architecture/` → stays relative) |
| `docs/ARCHITECTURE.md` → `docs/architecture/ARCHITECTURE.md` | `IMPLEMENTATION_ROADMAP.md` | `../releases/IMPLEMENTATION_ROADMAP.md` |
| `docs/ARCHITECTURE.md` → `docs/architecture/ARCHITECTURE.md` | `adr/ADR_INDEX.md` | `../adr/ADR_INDEX.md` |
| `docs/ARCHITECTURE.md` → `docs/architecture/ARCHITECTURE.md` | `adr/0008-pve-compatibility-matrix.md` | `../adr/0008-pve-compatibility-matrix.md` |
| `docs/IMPLEMENTATION_ROADMAP.md` → `docs/releases/IMPLEMENTATION_ROADMAP.md` | `ARCHITECTURE.md` | `../architecture/ARCHITECTURE.md` |
| `docs/IMPLEMENTATION_ROADMAP.md` → `docs/releases/IMPLEMENTATION_ROADMAP.md` | `MEMORY_KNOWLEDGE_MODEL.md` | `../architecture/MEMORY_KNOWLEDGE_MODEL.md` |
| `docs/IMPLEMENTATION_ROADMAP.md` → `docs/releases/IMPLEMENTATION_ROADMAP.md` | `adr/ADR_INDEX.md` | `../adr/ADR_INDEX.md` |
| `docs/MEMORY_KNOWLEDGE_MODEL.md` → `docs/architecture/MEMORY_KNOWLEDGE_MODEL.md` | `ARCHITECTURE.md` | `ARCHITECTURE.md` (same dir) |
| `docs/MEMORY_KNOWLEDGE_MODEL.md` → `docs/architecture/MEMORY_KNOWLEDGE_MODEL.md` | `IMPLEMENTATION_ROADMAP.md` | `../releases/IMPLEMENTATION_ROADMAP.md` |
| `docs/MEMORY_KNOWLEDGE_MODEL.md` → `docs/architecture/MEMORY_KNOWLEDGE_MODEL.md` | `adr/ADR_INDEX.md` | `../adr/ADR_INDEX.md` |
| `docs/README.md` | `implementation/PHASE_1A_TASK_PLAN.md` | `phase-1a/reports/PHASE_1A_TASK_PLAN.md` |
| `docs/adr/ADR_INDEX.md` | `../implementation/IMPLEMENTATION_PACKAGE.md` | `../phase-1a/reports/IMPLEMENTATION_PACKAGE.md` |
| `docs/adr/ADR_INDEX.md` | `../implementation/PHASE_1A_TASK_PLAN.md` | `../phase-1a/reports/PHASE_1A_TASK_PLAN.md` |
| `docs/adr/ADR_INDEX.md` | `../IMPLEMENTATION_ROADMAP.md` | `../releases/IMPLEMENTATION_ROADMAP.md` |
| `docs/adr/0001-implementation-language.md` | `../IMPLEMENTATION_ROADMAP.md` | `../releases/IMPLEMENTATION_ROADMAP.md` |
| `docs/adr/0001-implementation-language.md` | `../implementation/IMPLEMENTATION_PACKAGE.md` | `../phase-1a/reports/IMPLEMENTATION_PACKAGE.md` |
| `docs/adr/0002-mcp-transport.md` | `../ARCHITECTURE.md` | `../architecture/ARCHITECTURE.md` |
| `docs/adr/0002-mcp-transport.md` | `../IMPLEMENTATION_ROADMAP.md` | `../releases/IMPLEMENTATION_ROADMAP.md` |
| `docs/adr/0002-mcp-transport.md` | `../implementation/IMPLEMENTATION_PACKAGE.md` | `../phase-1a/reports/IMPLEMENTATION_PACKAGE.md` |
| `docs/implementation/IMPLEMENTATION_PACKAGE.md` → `docs/phase-1a/reports/IMPLEMENTATION_PACKAGE.md` | `PHASE_1A_TASK_PLAN.md` | `PHASE_1A_TASK_PLAN.md` (same dir) |
| `docs/implementation/PHASE_1A_TASK_PLAN.md` → `docs/phase-1a/reports/PHASE_1A_TASK_PLAN.md` | `../IMPLEMENTATION_ROADMAP.md` | `../../releases/IMPLEMENTATION_ROADMAP.md` |
| `docs/implementation/PHASE_1A_TASK_PLAN.md` → `docs/phase-1a/reports/PHASE_1A_TASK_PLAN.md` | `IMPLEMENTATION_PACKAGE.md` | `IMPLEMENTATION_PACKAGE.md` (same dir) |
| `docs/implementation/PHASE_1A_PROGRESS_REPORT.md` → `docs/phase-1a/reports/PHASE_1A_PROGRESS_REPORT.md` | `PHASE_1A_TASK_PLAN.md` | `PHASE_1A_TASK_PLAN.md` (same dir) |
| `docs/implementation/PHASE_1A_PROGRESS_REPORT.md` → `docs/phase-1a/reports/PHASE_1A_PROGRESS_REPORT.md` | `TECHNICAL_DEBT_REMEDIATION_REPORT.md` | `TECHNICAL_DEBT_REMEDIATION_REPORT.md` (same dir) |
| `docs/archive/README.md` | `../audit/DOCUMENTATION_CLEANUP_PLAN.md` | `DOCUMENTATION_CLEANUP_PLAN.md` (same dir) |
| `RELEASE_NOTES_v0.1.0-phase1a.md` → `docs/releases/RELEASE_NOTES_v0.1.0-phase1a.md` | `PHASE_1A_ACCEPTANCE.md` | `../phase-1a/acceptance/PHASE_1A_ACCEPTANCE.md` |
| `PHASE_1A_RELEASE_CHECKLIST.md` → `docs/phase-1a/reports/PHASE_1A_RELEASE_CHECKLIST.md` | References to root files | Prefix all local refs with `../../` or update to new paths |
| `TECHNICAL_DEBT_REMEDIATION_REPORT.md` → `docs/phase-1a/reports/TECHNICAL_DEBT_REMEDIATION_REPORT.md` | `CODEBASE_AUDIT_REPORT.md` | `../../archive/CODEBASE_AUDIT_REPORT.md` |
| `TECHNICAL_DEBT_REMEDIATION_REPORT.md` → `docs/phase-1a/reports/` | `docs/implementation/PHASE_1A_PROGRESS_REPORT.md` | `PHASE_1A_PROGRESS_REPORT.md` (same dir) |
| `INDEPENDENT_PROJECT_REVIEW.md` → `docs/archive/reviews/` | `CODEBASE_AUDIT_REPORT.md` | `../CODEBASE_AUDIT_REPORT.md` |
| `INDEPENDENT_PROJECT_REVIEW.md` → `docs/archive/reviews/` | `PHASE_1A_PROGRESS_REPORT.md` | `../../phase-1a/reports/PHASE_1A_PROGRESS_REPORT.md` |
| `CODEBASE_AUDIT_REPORT.md` → `docs/archive/` | `TECHNICAL_DEBT_REMEDIATION_REPORT.md` | `../phase-1a/reports/TECHNICAL_DEBT_REMEDIATION_REPORT.md` |
| `CODEBASE_AUDIT_REPORT.md` → `docs/archive/` | `docs/implementation/PHASE_1A_PROGRESS_REPORT.md` | `../phase-1a/reports/PHASE_1A_PROGRESS_REPORT.md` |
| `CODEBASE_AUDIT_REPORT.md` → `docs/archive/` | `docs/implementation/PHASE_1A_TASK_PLAN.md` | `../phase-1a/reports/PHASE_1A_TASK_PLAN.md` |

---

## 4. Execution Order

1. Create all target directories
2. Move files (git mv or copy + delete)
3. Update internal links in all affected files
4. Create/update `docs/README.md` as the documentation entry point
5. Remove empty source directories
6. Commit all changes

---

## 5. Verification

After execution:
- `git status` should show moved files (no deletions without corresponding additions)
- `git grep <old-path>` should find no dangling references
- All markdown links should resolve correctly
- `docs/README.md` should list all major sections

---

## 6. Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Broken external links (GitHub issues, blog posts) | Acceptable — internal repo links only |
| Merge conflicts with in-flight PRs | No active PRs — safe |
| Lost git history with `move` instead of `git mv` | Key architecture/ADR files use `git mv`; archive files use move+delete |
